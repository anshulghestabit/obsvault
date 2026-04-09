import argparse
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
from transformers import CLIPModel, CLIPProcessor  # noqa: E402

from src.config.settings import PROJECT_ROOT as SETTINGS_PROJECT_ROOT, TOP_K  # noqa: E402
from src.utils.helpers import clean_text  # noqa: E402


IMAGE_INDEX_FILE = SETTINGS_PROJECT_ROOT / "src" / "vectorstore" / "images" / "image_index.faiss"
IMAGE_STORE_FILE = SETTINGS_PROJECT_ROOT / "src" / "vectorstore" / "images" / "image_store.json"
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"


def get_device() -> str:
    """Return best available torch device."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_clip_components(
    model_name: str = CLIP_MODEL_NAME,
) -> tuple[CLIPProcessor, CLIPModel, str]:
    """Load CLIP model and processor."""
    device = get_device()
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name).to(device)
    model.eval()
    return processor, model, device


def load_index() -> faiss.Index:
    """Load image FAISS index."""
    if not IMAGE_INDEX_FILE.exists():
        raise FileNotFoundError(
            f"Image index not found: {IMAGE_INDEX_FILE}. Run clip_embedder.py first."
        )
    return faiss.read_index(str(IMAGE_INDEX_FILE))


def load_metadata() -> list[dict[str, Any]]:
    """Load image metadata store."""
    if not IMAGE_STORE_FILE.exists():
        raise FileNotFoundError(
            f"Image store not found: {IMAGE_STORE_FILE}. Run clip_embedder.py first."
        )

    with IMAGE_STORE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """L2-normalize vector."""
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def embed_text_query(
    query: str,
    processor: CLIPProcessor,
    model: CLIPModel,
    device: str,
) -> np.ndarray:
    """Embed text query with CLIP."""
    inputs = processor(text=[query], return_tensors="pt", padding=True)
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        features = model.get_text_features(**inputs)

    vector = features[0].detach().cpu().numpy().astype("float32")
    return normalize_vector(vector).astype("float32").reshape(1, -1)


def embed_image_query(
    image_path: Path,
    processor: CLIPProcessor,
    model: CLIPModel,
    device: str,
) -> np.ndarray:
    """Embed image query with CLIP."""
    if not image_path.exists():
        raise FileNotFoundError(f"Query image not found: {image_path}")

    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        features = model.get_image_features(**inputs)

    vector = features[0].detach().cpu().numpy().astype("float32")
    return normalize_vector(vector).astype("float32").reshape(1, -1)


def search_index(query_vector: np.ndarray, top_k: int) -> list[dict[str, Any]]:
    """Search image FAISS index and return ranked results."""
    index = load_index()
    metadata = load_metadata()

    scores, indices = index.search(query_vector, top_k)

    results: list[dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx < 0 or idx >= len(metadata):
            continue

        record = metadata[idx]
        results.append(
            {
                "score": float(score),
                "image_id": record["image_id"],
                "source": record["source"],
                "file_path": record["file_path"],
                "image_type": record["image_type"],
                "caption": record["caption"],
                "ocr_text": record["ocr_text"],
                "metadata": record.get("metadata", {}),
            }
        )

    return results


def text_to_image_search(query: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """Run text-to-image retrieval."""
    processor, model, device = load_clip_components()
    query_vector = embed_text_query(query, processor, model, device)
    return search_index(query_vector, top_k)


def image_to_image_search(image_path: Path, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """Run image-to-image retrieval."""
    processor, model, device = load_clip_components()
    query_vector = embed_image_query(image_path, processor, model, device)
    return search_index(query_vector, top_k)


def build_image_to_text_answer(results: list[dict[str, Any]]) -> str:
    """Build grounded answer text from retrieved image results."""
    if not results:
        return "No relevant images found."

    sections: list[str] = []
    for rank, item in enumerate(results, start=1):
        ocr_excerpt = item["ocr_text"][:500] if item["ocr_text"] else "No OCR text available."
        caption = item["caption"] or "No caption available."

        section = (
            f"Result {rank}\n"
            f"Source: {item['source']}\n"
            f"Score: {item['score']:.4f}\n"
            f"Caption: {caption}\n"
            f"OCR Excerpt: {clean_text(ocr_excerpt)}"
        )
        sections.append(section)

    return "\n\n".join(sections)


def print_results(results: list[dict[str, Any]]) -> None:
    """Pretty-print image search results."""
    if not results:
        print("No results found.")
        return

    for rank, item in enumerate(results, start=1):
        print(f"\nResult {rank}")
        print("-" * 90)
        print(f"Score     : {item['score']:.4f}")
        print(f"Image ID  : {item['image_id']}")
        print(f"Source    : {item['source']}")
        print(f"File Path : {item['file_path']}")
        print(f"Type      : {item['image_type']}")
        print(f"Metadata  : {item['metadata']}")
        print(f"Caption   : {item['caption']}")
        print("OCR Text:")
        print(item["ocr_text"][:700] if item["ocr_text"] else "No OCR text found.")
        if item["ocr_text"] and len(item["ocr_text"]) > 700:
            print("... [truncated]")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Multimodal image retrieval using CLIP + OCR + captions."
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["text-to-image", "image-to-image", "image-to-text"],
        help="Retrieval mode.",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Text query for text-to-image mode.",
    )
    parser.add_argument(
        "--image-path",
        type=str,
        default=None,
        help="Image path for image-to-image or image-to-text mode.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=TOP_K,
        help="Number of results to return.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.mode == "text-to-image":
        if not args.query:
            raise ValueError("--query is required for text-to-image mode.")
        results = text_to_image_search(query=args.query, top_k=args.top_k)
        print_results(results)
        return

    if args.mode == "image-to-image":
        if not args.image_path:
            raise ValueError("--image-path is required for image-to-image mode.")
        results = image_to_image_search(image_path=Path(args.image_path), top_k=args.top_k)
        print_results(results)
        return

    if args.mode == "image-to-text":
        if not args.image_path:
            raise ValueError("--image-path is required for image-to-text mode.")
        results = image_to_image_search(image_path=Path(args.image_path), top_k=args.top_k)
        answer = build_image_to_text_answer(results)
        print("\nImage-to-Text Answer")
        print("=" * 90)
        print(answer)
        return


if __name__ == "__main__":
    main()