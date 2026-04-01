import argparse
import json
import sys
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config.settings import TOP_K  # noqa: E402
from src.retriever.hybrid_retriever import parse_filters, retrieve  # noqa: E402
from src.retriever.reranker import rerank_pipeline  # noqa: E402


def build_context_text(results: list[dict[str, Any]]) -> str:
    """
    Build the final LLM context string from reranked results.

    Each chunk is clearly labeled for traceability.
    """
    sections: list[str] = []

    for rank, item in enumerate(results, start=1):
        section = (
            f"[Context {rank}]\n"
            f"Chunk ID: {item['chunk_id']}\n"
            f"Source: {item['source']}\n"
            f"Doc Type: {item['doc_type']}\n"
            f"Metadata: {item.get('metadata', {})}\n"
            f"Text:\n{item['text']}"
        )
        sections.append(section)

    return "\n\n" + ("\n\n" + ("-" * 80) + "\n\n").join(sections)


def build_traceable_sources(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Build compact traceable source records.

    These can be logged or passed to the generator layer later.
    """
    sources: list[dict[str, Any]] = []

    for item in results:
        sources.append(
            {
                "chunk_id": item["chunk_id"],
                "source": item["source"],
                "doc_type": item["doc_type"],
                "chunk_index": item["chunk_index"],
                "retrieval_method": item.get("retrieval_method"),
                "combined_score": item.get("combined_score"),
                "rerank_score": item.get("rerank_score"),
                "metadata": item.get("metadata", {}),
            }
        )

    return sources


def build_context_payload(
    query: str,
    top_k: int = TOP_K,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Full Day 2 context-building pipeline.

    Steps:
    - retrieve hybrid candidates
    - rerank and deduplicate
    - build final context text
    - return traceable source payload
    """
    candidates = retrieve(query=query, top_k=top_k, filters=filters)
    final_results = rerank_pipeline(query=query, candidates=candidates, top_k=top_k)

    context_text = build_context_text(final_results)
    sources = build_traceable_sources(final_results)

    return {
        "query": query,
        "top_k": top_k,
        "filters": filters or {},
        "context": context_text,
        "sources": sources,
    }


def print_payload(payload: dict[str, Any]) -> None:
    """Print the final context payload in a human-readable way."""
    print("\nQuery:")
    print(payload["query"])
    print("\nFilters:")
    print(payload["filters"])
    print("\nSources:")
    print(json.dumps(payload["sources"], indent=2, ensure_ascii=False))
    print("\nContext:")
    print(payload["context"])


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Build final traceable context using hybrid retrieval and reranking."
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
        help="Number of final chunks in context.",
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
    payload = build_context_payload(
        query=args.query,
        top_k=args.top_k,
        filters=filters,
    )
    print_payload(payload)


if __name__ == "__main__":
    main()