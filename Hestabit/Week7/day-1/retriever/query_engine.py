import argparse
import json
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import faiss  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402

from src.config.settings import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    FAISS_INDEX_FILE,
    QUERY_INSTRUCTION_PREFIX,
    TOP_K,
    VECTOR_METADATA_FILE,
)


def load_index() -> faiss.Index:
    """Load the FAISS vector index."""
    if not FAISS_INDEX_FILE.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {FAISS_INDEX_FILE}. Run embedder.py first."
        )
    return faiss.read_index(str(FAISS_INDEX_FILE))


def load_metadata() -> list[dict]:
    """Load chunk metadata stored alongside the FAISS index."""
    if not VECTOR_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {VECTOR_METADATA_FILE}. Run embedder.py first."
        )

    with VECTOR_METADATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def prepare_query_for_embedding(query: str) -> str:
    """
    Prepare query text for BGE retrieval embedding.

    For BGE models, short retrieval queries can benefit from a query instruction
    prefix. Document chunks should remain unprefixed.
    """
    return f"{QUERY_INSTRUCTION_PREFIX}{query.strip()}"


def embed_query(
    query: str,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
):
    """Embed and normalize a query for semantic search."""
    model = SentenceTransformer(model_name)
    model.max_seq_length = 512

    prepared_query = prepare_query_for_embedding(query)

    vector = model.encode(
        [prepared_query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return vector.astype("float32")


def search(query: str, top_k: int = TOP_K) -> list[dict]:
    """Search the FAISS index for the most relevant chunks."""
    index = load_index()
    metadata = load_metadata()
    query_vector = embed_query(query)

    scores, indices = index.search(query_vector, top_k)

    results: list[dict] = []
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx < 0 or idx >= len(metadata):
            continue

        chunk = metadata[idx]
        results.append(
            {
                "score": float(score),
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "doc_type": chunk["doc_type"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
            }
        )

    return results


def print_results(query: str, results: list[dict]) -> None:
    """Pretty-print retrieval results."""
    print(f"\nQuery: {query}")
    print("=" * 80)

    if not results:
        print("No results found.")
        return

    for rank, item in enumerate(results, start=1):
        print(f"\nResult {rank}")
        print("-" * 80)
        print(f"Score      : {item['score']:.4f}")
        print(f"Chunk ID   : {item['chunk_id']}")
        print(f"Source     : {item['source']}")
        print(f"Doc Type   : {item['doc_type']}")
        print(f"Chunk Index: {item['chunk_index']}")
        print("Text:")
        print(item["text"][:1000])
        if len(item["text"]) > 1000:
            print("... [truncated]")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query the FAISS index built from ingested documents."
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Natural language query string.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=TOP_K,
        help="Number of top results to return.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for CLI usage."""
    args = parse_args()
    results = search(query=args.query, top_k=args.top_k)
    print_results(args.query, results)


if __name__ == "__main__":
    main()