from typing import Any


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def context_match_score(answer: str, context: str) -> float:
    """
    Lightweight overlap-based context match score.

    Measures how much of the answer vocabulary appears in the retrieved context.
    """
    answer_tokens = set(normalize_text(answer).split())
    context_tokens = set(normalize_text(context).split())

    if not answer_tokens:
        return 0.0

    overlap = answer_tokens.intersection(context_tokens)
    return round(len(overlap) / len(answer_tokens), 4)


def faithfulness_score(answer: str, context: str) -> float:
    """
    Proxy faithfulness score.

    Uses token overlap between answer and context.
    """
    return context_match_score(answer, context)


def hallucination_detected(
    answer: str,
    context: str,
    threshold: float = 0.35,
) -> bool:
    """
    Flag likely hallucination if support from context is too low.
    """
    score = faithfulness_score(answer, context)
    return score < threshold


def confidence_score(
    answer: str,
    context: str,
    retrieved_items: list[dict[str, Any]] | None = None,
) -> float:
    """
    Combine faithfulness with retrieval score hints.
    """
    faithfulness = faithfulness_score(answer, context)

    retrieval_bonus = 0.0
    if retrieved_items:
        top_scores = []
        for item in retrieved_items[:3]:
            if "score" in item and item["score"] is not None:
                top_scores.append(float(item["score"]))
            elif "rerank_score" in item and item["rerank_score"] is not None:
                top_scores.append(float(item["rerank_score"]))

        if top_scores:
            retrieval_bonus = min(sum(top_scores) / len(top_scores), 1.0) * 0.2

    final_score = min(faithfulness + retrieval_bonus, 1.0)
    return round(final_score, 4)


def evaluate_answer(
    answer: str,
    context: str,
    retrieved_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Full evaluation bundle for Day 5.
    """
    match = context_match_score(answer, context)
    faithfulness = faithfulness_score(answer, context)
    hallucination = hallucination_detected(answer, context)
    confidence = confidence_score(answer, context, retrieved_items)

    return {
        "context_match_score": match,
        "faithfulness_score": faithfulness,
        "hallucination_detected": hallucination,
        "confidence_score": confidence,
    }