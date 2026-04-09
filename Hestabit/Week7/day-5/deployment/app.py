import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.evaluation.rag_eval import evaluate_answer
from src.memory.memory_store import MemoryStore

# Day 2
from src.pipelines.context_builder import build_context_payload

# Day 3
from src.retriever.image_search import (
    build_image_to_text_answer,
    image_to_image_search,
    text_to_image_search,
)

# Day 4
from src.pipelines.sql_pipeline import build_sql_pipeline_output


APP_TITLE = "Week 7 Capstone API"
CHAT_LOG_PATH = PROJECT_ROOT / "CHAT-LOGS.json"
MEMORY_FILE_PATH = PROJECT_ROOT / "src" / "memory" / "memory_sessions.json"

app = FastAPI(title=APP_TITLE)
memory_store = MemoryStore(file_path=MEMORY_FILE_PATH, max_messages=5)


class AskRequest(BaseModel):
    session_id: str = Field(..., description="Conversation session ID")
    query: str = Field(..., description="User query")
    top_k: int = Field(default=5, description="Number of context chunks")
    filters: dict[str, str] | None = Field(default=None, description="Optional retrieval filters")


class AskImageRequest(BaseModel):
    session_id: str = Field(..., description="Conversation session ID")
    mode: str = Field(..., description="text-to-image | image-to-image | image-to-text")
    query: str | None = Field(default=None, description="Text query for text-to-image")
    image_path: str | None = Field(default=None, description="Image path for image-based modes")
    top_k: int = Field(default=5, description="Number of results")


class AskSQLRequest(BaseModel):
    session_id: str = Field(..., description="Conversation session ID")
    question: str = Field(..., description="Natural language SQL question")
    db_path: str = Field(..., description="Path to SQLite DB")


def load_chat_logs() -> list[dict[str, Any]]:
    if not CHAT_LOG_PATH.exists():
        CHAT_LOG_PATH.write_text("[]", encoding="utf-8")

    with CHAT_LOG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_chat_logs(logs: list[dict[str, Any]]) -> None:
    with CHAT_LOG_PATH.open("w", encoding="utf-8") as file:
        json.dump(logs, file, ensure_ascii=False, indent=2)


def append_chat_log(entry: dict[str, Any]) -> None:
    logs = load_chat_logs()
    logs.append(entry)
    save_chat_logs(logs)


def build_text_answer(query: str, context_payload: dict[str, Any]) -> str:
    """
    Lightweight answer generator for the capstone.

    This is retrieval-grounded, not a full LLM answer generator.
    """
    sources = context_payload.get("sources", [])
    context = context_payload.get("context", "").strip()

    if not sources:
        return "I could not find relevant context for your question."

    answer_lines = [
        f"Answer for: {query}",
        "",
        "Based on the retrieved context, the most relevant information comes from these sources:",
    ]

    for source in sources[:3]:
        answer_lines.append( |----------------------------------|-------------|-------------| | Assets | | | | A. Property, plant and equipment | 19.6 | 20.0 | | B. Casual CGU | — | — | | C. Financials CGU | — | 487.4 | | D. Investment in associates | — | — | | | 19.6 | 507.4 | ## A. During 2021, the Group entered into a binding agreement for the disposal of a real estate area in Milan for a total consideration of €20.0 million. Accordingly, the real estate was classified as held for sale. Of the total consideration, €1.0 million was received during the year ended 31 December 2021. The advance received was classified as part of the liabilities directly associated with assets classified as held for sale. At the date of the transfer to assets held for sale, an impairment review was performed, where the carrying amount was compared to the fair value less expected disposal costs
            f"- {source['source']} | chunk_id={source['chunk_id']} | "
            f"score={source.get('rerank_score', source.get('combined_score'))}"
        )

    answer_lines.append("")
    answer_lines.append("Context-backed summary:")
    answer_lines.append(context[:1200])

    return "\n".join(answer_lines).strip()


def refine_answer(initial_answer: str, evaluation: dict[str, Any]) -> str:
    """
    Self-reflection / refinement loop.

    If confidence is low or hallucination is flagged, soften the answer.
    """
    if evaluation["hallucination_detected"] or evaluation["confidence_score"] < 0.45:
        return (
            initial_answer
            + "\n\nRefinement Note: This answer has limited grounding in the retrieved context. "
              "Please verify the cited sources before relying on it."
        )

    return initial_answer


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": APP_TITLE}


@app.post("/ask")
def ask_text(request: AskRequest) -> dict[str, Any]:
    memory_store.add_message(request.session_id, "user", request.query)

    context_payload = build_context_payload(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters,
    )

    initial_answer = build_text_answer(request.query, context_payload)
    evaluation = evaluate_answer(
        answer=initial_answer,
        context=context_payload.get("context", ""),
        retrieved_items=context_payload.get("sources", []),
    )
    final_answer = refine_answer(initial_answer, evaluation)

    memory_store.add_message(request.session_id, "assistant", final_answer)

    response = {
        "query": request.query,
        "answer": final_answer,
        "memory": memory_store.get_messages(request.session_id),
        "sources": context_payload.get("sources", []),
        "evaluation": evaluation,
        "debug": {
            "top_k": request.top_k,
            "filters": request.filters or {},
        },
    }

    append_chat_log(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "/ask",
            "session_id": request.session_id,
            "query": request.query,
            "response": response,
        }
    )

    return response


@app.post("/ask-image")
def ask_image(request: AskImageRequest) -> dict[str, Any]:
    memory_store.add_message(
        request.session_id,
        "user",
        request.query or request.image_path or request.mode,
    )

    if request.mode == "text-to-image":
        if not request.query:
            raise ValueError("query is required for text-to-image mode")

        results = text_to_image_search(request.query, top_k=request.top_k)
        answer = f"Retrieved {len(results)} image result(s) for text query: {request.query}"
        context = "\n".join(
            f"{item['caption']} {item['ocr_text']}" for item in results
        )

    elif request.mode == "image-to-image":
        if not request.image_path:
            raise ValueError("image_path is required for image-to-image mode")

        results = image_to_image_search(Path(request.image_path), top_k=request.top_k)
        answer = f"Retrieved {len(results)} visually similar image result(s)."
        context = "\n".join(
            f"{item['caption']} {item['ocr_text']}" for item in results
        )

    elif request.mode == "image-to-text":
        if not request.image_path:
            raise ValueError("image_path is required for image-to-text mode")

        results = image_to_image_search(Path(request.image_path), top_k=request.top_k)
        answer = build_image_to_text_answer(results)
        context = "\n".join(
            f"{item['caption']} {item['ocr_text']}" for item in results
        )

    else:
        raise ValueError("Unsupported image mode")

    evaluation = evaluate_answer(answer=answer, context=context, retrieved_items=results)
    final_answer = refine_answer(answer, evaluation)

    memory_store.add_message(request.session_id, "assistant", final_answer)

    response = {
        "mode": request.mode,
        "answer": final_answer,
        "results": results,
        "memory": memory_store.get_messages(request.session_id),
        "evaluation": evaluation,
    }

    append_chat_log(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "/ask-image",
            "session_id": request.session_id,
            "request": request.model_dump(),
            "response": response,
        }
    )

    return response


@app.post("/ask-sql")
def ask_sql(request: AskSQLRequest) -> dict[str, Any]:
    memory_store.add_message(request.session_id, "user", request.question)

    sql_output = build_sql_pipeline_output(
        db_path=request.db_path,
        question=request.question,
    )

    answer = sql_output["summary"]
    context = sql_output["generated_sql"]

    evaluation = evaluate_answer(answer=answer, context=context, retrieved_items=None)
    final_answer = refine_answer(answer, evaluation)

    memory_store.add_message(request.session_id, "assistant", final_answer)

    response = {
        "question": request.question,
        "answer": final_answer,
        "generated_sql": sql_output["generated_sql"],
        "reasoning": sql_output["generation_reasoning"],
        "memory": memory_store.get_messages(request.session_id),
        "evaluation": evaluation,
    }

    append_chat_log(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "/ask-sql",
            "session_id": request.session_id,
            "request": request.model_dump(),
            "response": response,
        }
    )

    return response