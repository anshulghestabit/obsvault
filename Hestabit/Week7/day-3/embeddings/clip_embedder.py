import json
import sys
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import faiss  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402
from tqdm import tqdm  # noqa: E402
from transformers import CLIPModel, CLIPProcessor  # noqa: E402

from src.config.settings import PROJECT_ROOT as SETTINGS_PROJECT_ROOT  # noqa: E402
from src.utils.helpers import read_jsonl  # noqa: E402


IMAGE_METADATA_FILE = SETTINGS_PROJECT_ROOT / "src" / "data" / "image_cleaned" / "image_documents.jsonl"
IMAGE_VECTORSTORE_DIR = SETTINGS_PROJECT_ROOT / "src" / "vectorstore" / "images"
IMAGE_INDEX_FILE = IMAGE_VECTORSTORE_DIR / "image_index.faiss"
IMAGE_STORE_FILE = IMAGE_VECTORSTORE_DIR / "image_store.json"

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"


def ensure_directories() -> None:
    """Create required vectorstore directories."""
    IMAGE_VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)


def get_device() -> str:
    """Return the best available torch device."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_clip_components(
    model_name: str = CLIP_MODEL_NAME,
) -> tuple[CLIPProcessor, CLIPModel, str]:
    """Load CLIP processor and model."""
    device = get_device()
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name).to(device)
    model.eval()
    return processor, model, device


def load_image_records() -> list[dict[str, Any]]:
    """Load image records created by image_ingest.py."""
    records = read_jsonl(IMAGE_METADATA_FILE)
    if not records:
        raise ValueError(f"No image records found in: {IMAGE_METADATA_FILE}")
    return records


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """L2-normalize a vector for cosine-like FAISS inner-product search."""
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def embed_image(
    image_path: Path,
    processor: CLIPProcessor,
    model: CLIPModel,
    device: str,
) -> np.ndarray:
    """Generate a normalized CLIP image embedding."""
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        features = model.get_image_features(**inputs)

    vector = features[0].detach().cpu().numpy().astype("float32")
    return normalize_vector(vector).astype("float32")


def build_embeddings(records: list[dict[str, Any]]) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Embed all images into one matrix."""
    processor, model, device = load_clip_components()
    embeddings: list[np.ndarray] = []

    for record in tqdm(records, desc="Embedding images with CLIP"):
        image_path = Path(record["file_path"])
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        vector = embed_image(image_path, processor, model, device)
        embeddings.append(vector)

    matrix = np.vstack(embeddings).astype("float32")
    return matrix, records


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """Build a FAISS index for normalized CLIP embeddings."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def save_metadata(records: list[dict[str, Any]]) -> None:
    """Save image metadata in the same order as the FAISS index."""
    with IMAGE_STORE_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def main() -> None:
    ensure_directories()

    records = load_image_records()
    embeddings, records = build_embeddings(records)
    index = build_faiss_index(embeddings)

    faiss.write_index(index, str(IMAGE_INDEX_FILE))
    save_metadata(records)

    print(f"[OK] CLIP image index saved to: {IMAGE_INDEX_FILE}")
    print(f"[OK] Image metadata store saved to: {IMAGE_STORE_FILE}")
    print(f"[INFO] Indexed images: {len(records)}")
    print(f"[INFO] Vector dimension: {embeddings.shape[1]}")


if __name__ == "__main__":
    main()