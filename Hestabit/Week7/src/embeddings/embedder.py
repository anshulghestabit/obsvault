import json
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import faiss  # noqa: E402
import numpy as np  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402

from src.config.settings import (  # noqa: E402
    CHUNKS_FILE,
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    FAISS_INDEX_FILE,
    VECTOR_METADATA_FILE,
    ensure_directories,
)
from src.utils.helpers import read_jsonl  # noqa: E402


def load_chunks() -> list[dict]:
    """
    Load chunk records created by the ingestion pipeline.
    """
    chunks = read_jsonl(CHUNKS_FILE)
    if not chunks:
        raise ValueError(f"No chunks found in: {CHUNKS_FILE}")
    return chunks


def build_embeddings(
    chunks: list[dict],
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> tuple[np.ndarray, list[dict]]:
    """
    Generate normalized embeddings for all chunks.

    Normalization allows IndexFlatIP to behave like cosine similarity.
    """
    texts = [chunk["text"] for chunk in chunks]

    model = SentenceTransformer(model_name)
    model.max_seq_length = 512

    embeddings = model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    if embeddings.ndim != 2:
        raise ValueError("Embeddings must be a 2D matrix.")

    return embeddings.astype("float32"), chunks


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build a FAISS inner-product index for normalized embeddings.
    """
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def save_metadata(chunks: list[dict]) -> None:
    """
    Save metadata in the same order as embeddings were indexed.
    """
    VECTOR_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with VECTOR_METADATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)


def main() -> None:
    ensure_directories()

    chunks = load_chunks()
    embeddings, chunks = build_embeddings(chunks)
    index = build_faiss_index(embeddings)

    FAISS_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_FILE))
    save_metadata(chunks)

    print(f"[OK] FAISS index saved to: {FAISS_INDEX_FILE}")
    print(f"[OK] Metadata saved to: {VECTOR_METADATA_FILE}")
    print(f"[INFO] Indexed chunks: {len(chunks)}")
    print(f"[INFO] Vector dimension: {embeddings.shape[1]}")


if __name__ == "__main__":
    main()