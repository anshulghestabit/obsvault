import argparse
import sys
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import numpy as np  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402

from src.config.settings import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    QUERY_INSTRUCTION_PREFIX,
    TOP_K,
)
from src.retriever.hybrid_retriever import retrieve  # noqa: E402


def prepare_query_for_embedding(query: str) -> str:
    """
    Prepare query text for BGE retrieval embedding.

    For BGE models, short retrieval queries can benefit from a query instruction
    prefix. Document chunks should remain unprefixed.
    """
    return f"{QUERY_INSTRUCTION_PREFIX}{query.strip()}"


def deduplicate_by_chunk_id(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove exact duplicates using chunk_id."""
    seen: set[str] = set()
    unique_items: list[dict[str, Any]] = []

    for item in candidates:
        chunk_id = item["chunk_id"]
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        unique_items.append(item)

    return unique_items


def deduplicate_by_text(
    candidates: list[dict[str, Any]],
    similarity_threshold: float = 0.95,
) -> list[dict[str, Any]]:
    """
    Remove near-duplicate texts using lightweight embedding similarity.

    This is useful when multiple chunks are almost identical.
    """
    if not candidates:
        return []

    model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
    model.max_seq_length = 512

    texts = [item["text"] for item in candidates]
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    kept_indices: list[int] = []

    for i, embedding in enumerate(embeddings):
        is_duplicate = False

        for kept_idx in kept_indices:
            similarity = float(np.dot(embedding, embeddings[kept_idx]))
            if similarity >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            kept_indices.append(i)

    return [candidates[i] for i in kept_indices]


def rerank_results(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = TOP_K,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict[str, Any]]:
    """
    Rerank candidates using query-to-chunk cosine similarity.

    This is simple, local, and reliable for Day 2.
    """
    if not candidates:
        return []

    model = SentenceTransformer(model_name)
    model.max_seq_length = 512

    texts = [item["text"] for item in candidates]
    prepared_query = prepare_query_for_embedding(query)

    query_embedding = model.encode(
        [prepared_query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0].astype("float32")

    chunk_embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    scored_items: list[dict[str, Any]] = []
    for item, embedding in zip(candidates, chunk_embeddings, strict=False):
        rerank_score = float(np.dot(query_embedding, embedding))
        updated_item = dict(item)
        updated_item["rerank_score"] = rerank_score
        scored_items.append(updated_item)

    scored_items.sort(key=lambda x: x["rerank_score"], reverse=True)
    return scored_items[: max(top_k * 2, top_k)]


def mmr_select(
    candidates: list[dict[str, Any]],
    query: str,
    top_k: int = TOP_K,
    lambda_param: float = 0.7,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict[str, Any]]:
    """
    Apply Max Marginal Relevance (MMR) to balance relevance and diversity.

    lambda_param:
    - closer to 1.0 => more relevance
    - closer to 0.0 => more diversity
    """
    if not candidates:
        return []

    model = SentenceTransformer(model_name)
    model.max_seq_length = 512

    texts = [item["text"] for item in candidates]
    prepared_query = prepare_query_for_embedding(query)

    query_embedding = model.encode(
        [prepared_query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0].astype("float32")

    doc_embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    selected_indices: list[int] = []
    remaining_indices = list(range(len(candidates)))

    while remaining_indices and len(selected_indices) < top_k:
        best_idx = None
        best_score = -float("inf")

        for idx in remaining_indices:
            relevance = float(np.dot(query_embedding, doc_embeddings[idx]))

            if not selected_indices:
                diversity_penalty = 0.0
            else:
                similarities = [
                    float(np.dot(doc_embeddings[idx], doc_embeddings[selected_idx]))
                    for selected_idx in selected_indices
                ]
                diversity_penalty = max(similarities)

            mmr_score = (lambda_param * relevance) - (
                (1.0 - lambda_param) * diversity_penalty
            )

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is None:
            break

        selected_indices.append(best_idx)
        remaining_indices.remove(best_idx)

    selected_items: list[dict[str, Any]] = []
    for idx in selected_indices:
        item = dict(candidates[idx])
        item["mmr_selected"] = True
        selected_items.append(item)

    return selected_items


def rerank_pipeline(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    """
    Full Day 2 reranking pipeline:
    - deduplicate by chunk_id
    - deduplicate by near-text similarity
    - rerank by query similarity
    - diversify with MMR
    """
    unique_by_id = deduplicate_by_chunk_id(candidates)
    unique_by_text = deduplicate_by_text(unique_by_id)
    reranked = rerank_results(query=query, candidates=unique_by_text, top_k=top_k)
    final_results = mmr_select(query=query, candidates=reranked, top_k=top_k)
    return final_results


def print_results(query: str, results: list[dict[str, Any]]) -> None:
    """Pretty-print reranked results."""
    print(f"\nQuery: {query}")
    print("=" * 90)

    if not results:
        print("No reranked results found.")
        return

    for rank, item in enumerate(results, start=1):
        print(f"\nFinal Result {rank}")
        print("-" * 90)
        print(f"Chunk ID      : {item['chunk_id']}")
        print(f"Source        : {item['source']}")
        print(f"Method        : {item['retrieval_method']}")
        print(f"Combined Score: {item.get('combined_score')}")
        print(f"Rerank Score  : {item.get('rerank_score')}")
        print(f"Metadata      : {item.get('metadata')}")
        print("Text:")
        print(item["text"][:700])
        if len(item["text"]) > 700:
            print("... [truncated]")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Rerank hybrid retrieval candidates."
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
        help="Number of final reranked results.",
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
    candidates = retrieve(query=args.query, top_k=args.top_k, filters=None)
    final_results = rerank_pipeline(
        query=args.query,
        candidates=candidates,
        top_k=args.top_k,
    )
    print_results(args.query, final_results)


if __name__ == "__main__":
    main()