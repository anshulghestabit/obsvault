import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import faiss  # noqa: E402
import numpy as np  # noqa: E402
from rank_bm25 import BM25Okapi  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402

from src.config.settings import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    FAISS_INDEX_FILE,
    QUERY_INSTRUCTION_PREFIX,
    TOP_K,
    VECTOR_METADATA_FILE,
)


def normalize_text(text: str) -> str:
    """Normalize text for lightweight matching and tokenization."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize_for_bm25(text: str) -> list[str]:
    """Simple BM25 tokenizer."""
    text = normalize_text(text)
    return re.findall(r"\b[a-zA-Z0-9]+\b", text)


def prepare_query_for_embedding(query: str) -> str:
    """
    Prepare query text for BGE retrieval embedding.

    For BGE models, short retrieval queries can benefit from a query instruction
    prefix. Document chunks should remain unprefixed.
    """
    return f"{QUERY_INSTRUCTION_PREFIX}{query.strip()}"


def load_index() -> faiss.Index:
    """Load the FAISS vector index."""
    if not FAISS_INDEX_FILE.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {FAISS_INDEX_FILE}. Run embedder.py first."
        )
    return faiss.read_index(str(FAISS_INDEX_FILE))


def load_metadata() -> list[dict[str, Any]]:
    """Load chunk metadata stored alongside the FAISS index."""
    if not VECTOR_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {VECTOR_METADATA_FILE}. Run embedder.py first."
        )

    with VECTOR_METADATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def embed_query(
    query: str,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> np.ndarray:
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


def infer_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    """
    Enrich chunk metadata with simple inferred fields.

    This keeps Day 2 practical without forcing a Day 1 ingestion rewrite.
    """
    source = chunk.get("source", "")
    text = chunk.get("text", "")
    doc_type = chunk.get("doc_type", "")

    combined = f"{source} {text[:1000]}"
    year_match = re.search(r"\b(19|20)\d{2}\b", combined)
    inferred_year = year_match.group(0) if year_match else None

    inferred_type = "general"
    lower_combined = combined.lower()

    if "policy" in lower_combined:
        inferred_type = "policy"
    elif "report" in lower_combined:
        inferred_type = "report"
    elif "financial" in lower_combined:
        inferred_type = "financial"
    elif "governance" in lower_combined:
        inferred_type = "governance"

    metadata = dict(chunk.get("metadata", {}))
    metadata["year"] = metadata.get("year") or inferred_year
    metadata["type"] = metadata.get("type") or inferred_type
    metadata["doc_type"] = metadata.get("doc_type") or doc_type
    metadata["source"] = metadata.get("source") or source

    return metadata


def semantic_search(
    query: str,
    metadata: list[dict[str, Any]],
    top_k: int = TOP_K,
    candidate_multiplier: int = 4,
) -> list[dict[str, Any]]:
    """
    Retrieve semantic candidates from FAISS.

    We retrieve more than top_k so later filtering and reranking have room to work.
    """
    index = load_index()
    query_vector = embed_query(query)

    search_k = max(top_k * candidate_multiplier, top_k)
    scores, indices = index.search(query_vector, search_k)

    results: list[dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx < 0 or idx >= len(metadata):
            continue

        chunk = metadata[idx]
        results.append(
            {
                "retrieval_method": "semantic",
                "semantic_score": float(score),
                "keyword_score": None,
                "combined_score": float(score),
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "doc_type": chunk["doc_type"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "metadata": infer_metadata(chunk),
            }
        )

    return results


def build_bm25(metadata: list[dict[str, Any]]) -> tuple[BM25Okapi, list[list[str]]]:
    """Build BM25 model from chunk texts."""
    tokenized_corpus = [tokenize_for_bm25(chunk["text"]) for chunk in metadata]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, tokenized_corpus


def keyword_search(
    query: str,
    metadata: list[dict[str, Any]],
    top_k: int = TOP_K,
    candidate_multiplier: int = 4,
) -> list[dict[str, Any]]:
    """
    Retrieve keyword candidates using BM25.

    This acts as both a complement and a fallback for semantic retrieval.
    """
    bm25, _ = build_bm25(metadata)
    query_tokens = tokenize_for_bm25(query)
    scores = bm25.get_scores(query_tokens)

    if len(scores) == 0:
        return []

    ranked_indices = np.argsort(scores)[::-1]
    search_k = max(top_k * candidate_multiplier, top_k)

    results: list[dict[str, Any]] = []
    for idx in ranked_indices[:search_k]:
        chunk = metadata[int(idx)]
        score = float(scores[int(idx)])

        results.append(
            {
                "retrieval_method": "keyword",
                "semantic_score": None,
                "keyword_score": score,
                "combined_score": score,
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "doc_type": chunk["doc_type"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "metadata": infer_metadata(chunk),
            }
        )

    return results


def passes_filters(item: dict[str, Any], filters: dict[str, str] | None) -> bool:
    """Return True if a retrieved item satisfies metadata filters."""
    if not filters:
        return True

    metadata = item.get("metadata", {})
    for key, expected_value in filters.items():
        actual_value = metadata.get(key)

        if actual_value is None:
            return False

        if str(actual_value).lower() != str(expected_value).lower():
            return False

    return True


def apply_filters(
    results: list[dict[str, Any]],
    filters: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Apply metadata filters to retrieved results."""
    return [item for item in results if passes_filters(item, filters)]


def merge_results(
    semantic_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merge semantic and keyword results by chunk_id.

    If a chunk appears in both sets, combine evidence and keep both scores.
    """
    merged: dict[str, dict[str, Any]] = {}

    for item in semantic_results:
        merged[item["chunk_id"]] = dict(item)

    for item in keyword_results:
        chunk_id = item["chunk_id"]

        if chunk_id in merged:
            merged_item = merged[chunk_id]
            merged_item["retrieval_method"] = "hybrid"
            merged_item["keyword_score"] = item["keyword_score"]

            semantic_score = merged_item["semantic_score"] or 0.0
            keyword_score = item["keyword_score"] or 0.0

            merged_item["combined_score"] = semantic_score + keyword_score
        else:
            merged[chunk_id] = dict(item)

    merged_results = list(merged.values())
    merged_results.sort(key=lambda x: x["combined_score"], reverse=True)
    return merged_results


def retrieve(
    query: str,
    top_k: int = TOP_K,
    filters: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Run hybrid retrieval:
    - semantic search
    - keyword search
    - merge
    - filter
    - return top candidates
    """
    metadata = load_metadata()

    semantic_results = semantic_search(query=query, metadata=metadata, top_k=top_k)
    keyword_results = keyword_search(query=query, metadata=metadata, top_k=top_k)

    merged_results = merge_results(semantic_results, keyword_results)
    filtered_results = apply_filters(merged_results, filters=filters)

    if not filtered_results:
        # Keyword fallback and relaxed behavior:
        # if strict filters eliminate everything, fall back to unfiltered merged results.
        filtered_results = merged_results

    return filtered_results[: max(top_k * 3, top_k)]


def parse_filters(raw_filters: str | None) -> dict[str, str] | None:
    """
    Parse filters from JSON string input.

    Example:
    --filters '{"year":"2024","type":"policy"}'
    """
    if not raw_filters:
        return None

    try:
        parsed = json.loads(raw_filters)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Filters must be valid JSON. Example: "
            '\'{"year":"2024","type":"policy"}\''
        ) from error

    if not isinstance(parsed, dict):
        raise ValueError("Filters JSON must decode to a dictionary.")

    return {str(key): str(value) for key, value in parsed.items()}


def print_results(query: str, results: list[dict[str, Any]]) -> None:
    """Pretty-print retrieval candidates."""
    print(f"\nQuery: {query}")
    print("=" * 90)

    if not results:
        print("No results found.")
        return

    for rank, item in enumerate(results, start=1):
        print(f"\nCandidate {rank}")
        print("-" * 90)
        print(f"Method       : {item['retrieval_method']}")
        print(f"Combined     : {item['combined_score']:.4f}")
        print(f"Semantic     : {item['semantic_score']}")
        print(f"Keyword      : {item['keyword_score']}")
        print(f"Chunk ID     : {item['chunk_id']}")
        print(f"Source       : {item['source']}")
        print(f"Doc Type     : {item['doc_type']}")
        print(f"Chunk Index  : {item['chunk_index']}")
        print(f"Metadata     : {item['metadata']}")
        print("Text:")
        print(item["text"][:700])
        if len(item["text"]) > 700:
            print("... [truncated]")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run hybrid retrieval using FAISS + BM25."
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
        help="Number of desired top results.",
    )
    parser.add_argument(
        "--filters",
        type=str,
        default=None,
        help='Optional JSON filters, e.g. \'{"year":"2024","type":"policy"}\'',
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line usage."""
    args = parse_args()
    filters = parse_filters(args.filters)
    results = retrieve(query=args.query, top_k=args.top_k, filters=filters)
    print_results(args.query, results)


if __name__ == "__main__":
    main()