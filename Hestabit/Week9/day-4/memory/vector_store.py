from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import faiss
import numpy as np
from openai import AsyncOpenAI

from autogen_core.memory import (
    MemoryContent,
    MemoryMimeType,
    MemoryQueryResult,
    UpdateContextResult,
)
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import SystemMessage, UserMessage

from memory.sqlite_store import SQLiteStore


class LMStudioEmbeddingClient:
    """
    Uses LM Studio's OpenAI-compatible /v1/embeddings endpoint.
    """

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        cleaned = [(text or "").replace("\n", " ").strip() for text in texts]
        cleaned = [text for text in cleaned if text]
        if not cleaned:
            return np.zeros((0, 0), dtype=np.float32)

        response = await self.client.embeddings.create(
            model=self.model,
            input=cleaned,
        )
        vectors = np.array([item.embedding for item in response.data], dtype=np.float32)
        faiss.normalize_L2(vectors)
        return vectors

    async def close(self) -> None:
        await self.client.close()


class FaissSQLiteMemory:
    """
    Custom AutoGen-compatible memory store.

    - Long-term storage lives in SQLite
    - Similarity search lives in FAISS
    - update_context() injects retrieved memory into the AssistantAgent context
    """

    def __init__(
        self,
        sqlite_store: SQLiteStore,
        base_url: str,
        api_key: str,
        embed_model: str,
        faiss_index_path: str = "memory/faiss.index",
        faiss_meta_path: str = "memory/faiss_meta.json",
        k: int = 4,
        score_threshold: float = 0.35,
    ) -> None:
        self.sqlite_store = sqlite_store
        self.embedder = LMStudioEmbeddingClient(
            base_url=base_url,
            api_key=api_key,
            model=embed_model,
        )
        self.index_path = Path(faiss_index_path)
        self.meta_path = Path(faiss_meta_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)

        self.k = max(1, k)
        self.score_threshold = float(score_threshold)
        self.index: faiss.IndexFlatIP | None = None
        self.records: list[dict[str, Any]] = []

        self._load()

    def _load(self) -> None:
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.records = json.loads(self.meta_path.read_text(encoding="utf-8"))
        else:
            self.index = None
            self.records = []

    def _save(self) -> None:
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(
            json.dumps(self.records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)

    @staticmethod
    def _coerce_text(value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    async def remember_conversation(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        return self.sqlite_store.add_conversation(role=role, content=content, metadata=metadata)

    async def remember_fact(
        self,
        content: str,
        category: str = "semantic",
        source_turn_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        text = self._coerce_text(content)
        if not text:
            raise ValueError("Cannot store an empty fact.")

        memory_id = self.sqlite_store.add_fact(
            content=text,
            category=category,
            source_turn_id=source_turn_id,
            metadata=metadata,
        )

        vectors = await self.embedder.embed_texts([text])
        if vectors.size == 0:
            return memory_id

        self._ensure_index(vectors.shape[1])
        assert self.index is not None
        self.index.add(vectors)

        self.records.append(
            {
                "memory_id": memory_id,
                "category": category,
                "source_turn_id": source_turn_id,
                "content_preview": text[:200],
            }
        )
        self._save()
        return memory_id

    async def add(self, content: MemoryContent, cancellation_token: Any = None) -> None:
        text = self._coerce_text(content.content)
        metadata = dict(content.metadata or {})
        kind = metadata.get("kind", "fact")

        if not text:
            return

        if kind == "conversation":
            role = metadata.get("role", "assistant")
            await self.remember_conversation(role=role, content=text, metadata=metadata)
        else:
            await self.remember_fact(
                content=text,
                category=metadata.get("category", "semantic"),
                source_turn_id=metadata.get("source_turn_id"),
                metadata=metadata,
            )

    async def query(
        self,
        query: str | MemoryContent,
        cancellation_token: Any = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        query_text = query.content if isinstance(query, MemoryContent) else query
        query_text = self._coerce_text(query_text)

        if not query_text or self.index is None or not self.records:
            return MemoryQueryResult(results=[])

        top_k = int(kwargs.get("k", self.k))
        score_threshold = float(kwargs.get("score_threshold", self.score_threshold))

        query_vector = await self.embedder.embed_texts([query_text])
        if query_vector.size == 0:
            return MemoryQueryResult(results=[])

        scores, indices = self.index.search(query_vector, min(top_k, len(self.records)))
        selected: list[tuple[int, float]] = []
        seen: set[int] = set()

        for score, idx in zip(scores[0].tolist(), indices[0].tolist()):
            if idx < 0:
                continue
            if float(score) < score_threshold:
                continue

            memory_id = int(self.records[idx]["memory_id"])
            if memory_id in seen:
                continue

            seen.add(memory_id)
            selected.append((memory_id, float(score)))

        rows = self.sqlite_store.get_by_ids([memory_id for memory_id, _ in selected])
        row_map = {row.id: row for row in rows}

        results: list[MemoryContent] = []
        for memory_id, score in selected:
            row = row_map.get(memory_id)
            if row is None:
                continue

            results.append(
                MemoryContent(
                    content=row.content,
                    mime_type=MemoryMimeType.TEXT,
                    metadata={
                        "memory_id": row.id,
                        "kind": row.kind,
                        "category": row.category,
                        "source_turn_id": row.source_turn_id,
                        "score": score,
                    },
                )
            )

        return MemoryQueryResult(results=results)

    async def update_context(self, model_context: ChatCompletionContext) -> UpdateContextResult:
        messages = await model_context.get_messages()

        latest_user_query = ""
        for message in reversed(messages):
            if isinstance(message, UserMessage):
                latest_user_query = self._coerce_text(message.content)
                if latest_user_query:
                    break

        if not latest_user_query:
            return UpdateContextResult(memories=MemoryQueryResult(results=[]))

        memory_result = await self.query(latest_user_query)
        if not memory_result.results:
            return UpdateContextResult(memories=memory_result)

        lines = ["Relevant long-term memory retrieved for this query:"]
        for i, item in enumerate(memory_result.results, start=1):
            category = (item.metadata or {}).get("category", "semantic")
            score = float((item.metadata or {}).get("score", 0.0))
            lines.append(f"{i}. [{category}] {item.content} (score={score:.3f})")

        await model_context.add_message(SystemMessage(content="\n".join(lines)))
        return UpdateContextResult(memories=memory_result)

    async def clear(self) -> None:
        self.sqlite_store.clear()
        self.index = None
        self.records = []

        if self.index_path.exists():
            self.index_path.unlink()
        if self.meta_path.exists():
            self.meta_path.unlink()

    async def close(self) -> None:
        await self.embedder.close()
        self.sqlite_store.close()
        