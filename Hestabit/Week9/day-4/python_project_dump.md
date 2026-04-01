# Python Project Dump

## Folder Structure
```
.
├── data
├── .env
├── files.zip
├── .gitignore
├── logs
├── memory
│   ├── faiss.index
│   ├── faiss_meta.json
│   ├── __init__.py
│   ├── long_term.db
│   ├── session_memory.py
│   ├── sqlite_store.py
│   └── vector_store.py
├── MEMORY-SYSTEM.md
├── orchestrator
│   ├── __init__.py
│   └── memory_orchestrator.py
├── python_project_dump.md
└── requirements.txt

5 directories, 15 files
```

## FILE: ./memory/__init__.py

```py
from .session_memory import SessionMemory, SessionMessage
from .sqlite_store import SQLiteStore, MemoryRow
from .vector_store import FaissSQLiteMemory

__all__ = [
    "SessionMemory",
    "SessionMessage",
    "SQLiteStore",
    "MemoryRow",
    "FaissSQLiteMemory",
]
```

## FILE: ./memory/session_memory.py

```py
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Literal

Role = Literal["user", "assistant", "system"]


@dataclass(slots=True)
class SessionMessage:
    role: Role
    content: str


class SessionMemory:
    """
    Simple short-term session memory.
    Keeps only the most recent N messages in memory.
    """

    def __init__(self, window_size: int = 10) -> None:
        self.window_size = max(1, window_size)
        self._messages: Deque[SessionMessage] = deque(maxlen=self.window_size)

    def add(self, role: Role, content: str) -> None:
        text = (content or "").strip()
        if not text:
            return
        self._messages.append(SessionMessage(role=role, content=text))

    def add_user(self, content: str) -> None:
        self.add("user", content)

    def add_assistant(self, content: str) -> None:
        self.add("assistant", content)

    def add_system(self, content: str) -> None:
        self.add("system", content)

    def clear(self) -> None:
        self._messages.clear()

    def get_messages(self) -> List[SessionMessage]:
        return list(self._messages)

    def render_for_prompt(self) -> str:
        if not self._messages:
            return "No recent session context."

        lines: list[str] = []
        for i, message in enumerate(self._messages, start=1):
            lines.append(f"{i}. {message.role.upper()}: {message.content}")
        return "\n".join(lines)
```

## FILE: ./memory/sqlite_store.py

```py
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class MemoryRow:
    id: int
    kind: str
    role: str | None
    content: str
    category: str | None
    source_turn_id: str | None
    metadata_json: str | None
    created_at: float


class SQLiteStore:
    """
    Long-term persistent memory using SQLite.
    Stores:
    - conversation messages
    - extracted/summarized facts
    """

    def __init__(self, db_path: str = "memory/long_term.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,                -- conversation | fact
                role TEXT,                         -- user | assistant | system | NULL
                content TEXT NOT NULL,
                category TEXT,                     -- episodic | semantic | preference | project | constraint
                source_turn_id TEXT,
                metadata_json TEXT,
                created_at REAL NOT NULL
            )
            """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_turn_id ON memories(source_turn_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at)"
        )

        self.conn.commit()

    def add_conversation(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (kind, role, content, category, source_turn_id, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "conversation",
                role,
                content,
                "episodic",
                (metadata or {}).get("source_turn_id"),
                json.dumps(metadata or {}, ensure_ascii=False),
                time.time(),
            ),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def add_fact(
        self,
        content: str,
        category: str = "semantic",
        source_turn_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        cursor = self.conn.cursor()
        payload = dict(metadata or {})
        payload["category"] = category
        cursor.execute(
            """
            INSERT INTO memories (kind, role, content, category, source_turn_id, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "fact",
                None,
                content,
                category,
                source_turn_id,
                json.dumps(payload, ensure_ascii=False),
                time.time(),
            ),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def get_by_ids(self, ids: Iterable[int]) -> list[MemoryRow]:
        ids = [int(x) for x in ids]
        if not ids:
            return []

        placeholders = ",".join("?" for _ in ids)
        cursor = self.conn.cursor()
        rows = cursor.execute(
            f"""
            SELECT id, kind, role, content, category, source_turn_id, metadata_json, created_at
            FROM memories
            WHERE id IN ({placeholders})
            """,
            ids,
        ).fetchall()

        return [
            MemoryRow(
                id=row["id"],
                kind=row["kind"],
                role=row["role"],
                content=row["content"],
                category=row["category"],
                source_turn_id=row["source_turn_id"],
                metadata_json=row["metadata_json"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_recent_conversations(self, limit: int = 20) -> list[MemoryRow]:
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """
            SELECT id, kind, role, content, category, source_turn_id, metadata_json, created_at
            FROM memories
            WHERE kind = 'conversation'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            MemoryRow(
                id=row["id"],
                kind=row["kind"],
                role=row["role"],
                content=row["content"],
                category=row["category"],
                source_turn_id=row["source_turn_id"],
                metadata_json=row["metadata_json"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_recent_facts(self, limit: int = 20) -> list[MemoryRow]:
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """
            SELECT id, kind, role, content, category, source_turn_id, metadata_json, created_at
            FROM memories
            WHERE kind = 'fact'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            MemoryRow(
                id=row["id"],
                kind=row["kind"],
                role=row["role"],
                content=row["content"],
                category=row["category"],
                source_turn_id=row["source_turn_id"],
                metadata_json=row["metadata_json"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def clear(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
```

## FILE: ./memory/vector_store.py

```py
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
        
```

## FILE: ./orchestrator/__init__.py

```py

```

## FILE: ./orchestrator/memory_orchestrator.py

```py
from __future__ import annotations

import asyncio
import os
import uuid

from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from memory.session_memory import SessionMemory
from memory.sqlite_store import SQLiteStore
from memory.vector_store import FaissSQLiteMemory


ANSWER_SYSTEM_PROMPT = """
You are a memory-aware local AI assistant running on LM Studio.

Rules:
1. Use the current user query first.
2. Use recent session context when useful.
3. Use retrieved long-term memory only when relevant.
4. Never invent memories that were not retrieved or provided in the current session.
5. If retrieved memory conflicts with the user's latest message, prefer the latest user message.
6. Be concise, direct, and helpful.
""".strip()


FACT_EXTRACTOR_SYSTEM_PROMPT = """
You extract durable, memory-worthy facts from a single user/assistant exchange.

Keep only stable items worth remembering later, such as:
- preferences
- constraints
- project goals
- ongoing tasks
- personal work context
- durable decisions

Do NOT store:
- temporary greetings
- filler language
- obvious restatements
- one-off conversational fluff

Return only bullet points in exactly this format:
- fact text | category=semantic

Allowed categories:
semantic, preference, constraint, project, episodic
""".strip()


class MemoryOrchestrator:
    def __init__(self) -> None:
        load_dotenv()

        base_url = os.environ["LM_STUDIO_BASE_URL"]
        api_key = os.environ.get("LM_STUDIO_API_KEY", "lm-studio")
        chat_model = os.environ["LM_STUDIO_CHAT_MODEL"]
        embed_model = os.environ["LM_STUDIO_EMBED_MODEL"]

        session_window_size = int(os.environ.get("SESSION_WINDOW_SIZE", "10"))
        top_k = int(os.environ.get("VECTOR_TOP_K", "4"))
        score_threshold = float(os.environ.get("VECTOR_SCORE_THRESHOLD", "0.35"))

        sqlite_db_path = os.environ.get("SQLITE_DB_PATH", "memory/long_term.db")
        faiss_index_path = os.environ.get("FAISS_INDEX_PATH", "memory/faiss.index")
        faiss_meta_path = os.environ.get("FAISS_META_PATH", "memory/faiss_meta.json")

        self.session_memory = SessionMemory(window_size=session_window_size)
        self.sqlite_store = SQLiteStore(db_path=sqlite_db_path)
        self.long_term_memory = FaissSQLiteMemory(
            sqlite_store=self.sqlite_store,
            base_url=base_url,
            api_key=api_key,
            embed_model=embed_model,
            faiss_index_path=faiss_index_path,
            faiss_meta_path=faiss_meta_path,
            k=top_k,
            score_threshold=score_threshold,
        )

        model_info = {
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "structured_output": False,
            "family": "qwen",
            "multiple_system_messages": True,
        }

        self.answer_model_client = OpenAIChatCompletionClient(
            model=chat_model,
            base_url=base_url,
            api_key=api_key,
            model_info=model_info,
        )

        self.fact_model_client = OpenAIChatCompletionClient(
            model=chat_model,
            base_url=base_url,
            api_key=api_key,
            model_info=model_info,
        )

        self.answer_agent = AssistantAgent(
            name="memory_answer_agent",
            system_message=ANSWER_SYSTEM_PROMPT,
            model_client=self.answer_model_client,
            memory=[self.long_term_memory],
        )

        self.fact_extractor_agent = AssistantAgent(
            name="memory_fact_extractor",
            system_message=FACT_EXTRACTOR_SYSTEM_PROMPT,
            model_client=self.fact_model_client,
        )

    def _build_task(self, user_query: str) -> str:
        session_context = self.session_memory.render_for_prompt()
        return f"""
Recent short-term session context:
{session_context}

Current user query:
{user_query}

Answer the current query naturally.
Use relevant memory only when it genuinely helps.
""".strip()

    @staticmethod
    def _extract_final_text(task_result: object) -> str:
        messages = getattr(task_result, "messages", [])
        for message in reversed(messages):
            content = getattr(message, "content", None)
            if isinstance(content, str) and content.strip():
                return content.strip()
        return "I could not generate a valid response."

    @staticmethod
    def _parse_fact_lines(text: str) -> list[tuple[str, str]]:
        facts: list[tuple[str, str]] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue

            body = stripped[2:].strip()
            if not body:
                continue

            if "| category=" in body:
                fact_text, category = body.rsplit("| category=", 1)
                fact_text = fact_text.strip()
                category = category.strip().lower()
            else:
                fact_text = body
                category = "semantic"

            if fact_text:
                facts.append((fact_text, category))

        # keep memory tight
        return facts[:5]

    async def _store_exchange(self, turn_id: str, user_query: str, answer: str) -> None:
        await self.long_term_memory.remember_conversation(
            role="user",
            content=user_query,
            metadata={"source_turn_id": turn_id, "kind": "conversation"},
        )
        await self.long_term_memory.remember_conversation(
            role="assistant",
            content=answer,
            metadata={"source_turn_id": turn_id, "kind": "conversation"},
        )

    async def _extract_and_store_facts(self, turn_id: str, user_query: str, answer: str) -> None:
        extraction_prompt = f"""
Interaction to analyze:

USER:
{user_query}

ASSISTANT:
{answer}

Extract only durable facts worth saving for future recall.
Return only bullet points in the required format.
If nothing is worth storing, return an empty response.
""".strip()

        result = await self.fact_extractor_agent.run(task=extraction_prompt)
        raw_text = self._extract_final_text(result)
        facts = self._parse_fact_lines(raw_text)

        for fact_text, category in facts:
            await self.long_term_memory.remember_fact(
                content=fact_text,
                category=category,
                source_turn_id=turn_id,
                metadata={"kind": "fact", "source": "fact_extractor"},
            )

    async def ask(self, user_query: str) -> str:
        turn_id = str(uuid.uuid4())

        self.session_memory.add_user(user_query)

        result = await self.answer_agent.run(task=self._build_task(user_query))
        answer = self._extract_final_text(result)

        self.session_memory.add_assistant(answer)

        await self._store_exchange(turn_id=turn_id, user_query=user_query, answer=answer)
        await self._extract_and_store_facts(turn_id=turn_id, user_query=user_query, answer=answer)

        return answer

    async def print_recent_facts(self, limit: int = 10) -> None:
        rows = self.sqlite_store.get_recent_facts(limit=limit)
        if not rows:
            print("No stored facts found.")
            return

        print("\nRecent facts:")
        for row in rows:
            print(f"- [{row.category}] {row.content}")

    async def close(self) -> None:
        await self.answer_model_client.close()
        await self.fact_model_client.close()
        await self.long_term_memory.close()


async def interactive_cli() -> None:
    orchestrator = MemoryOrchestrator()

    print("\nDay 4 Memory Orchestrator is ready.")
    print("Commands:")
    print("  /session  -> show short-term session memory")
    print("  /facts    -> show recent long-term facts")
    print("  /exit     -> quit\n")

    try:
        while True:
            user_query = input("You: ").strip()

            if not user_query:
                continue

            if user_query.lower() in {"/exit", "exit", "quit"}:
                break

            if user_query.lower() == "/session":
                print("\nShort-term session memory:")
                print(orchestrator.session_memory.render_for_prompt())
                print()
                continue

            if user_query.lower() == "/facts":
                await orchestrator.print_recent_facts(limit=10)
                print()
                continue

            answer = await orchestrator.ask(user_query)
            print(f"\nAssistant: {answer}\n")

    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(interactive_cli())
```

## FILE: ./requirements.txt

```txt
autogen-agentchat
autogen-ext[openai]
faiss-cpu
sentence-transformers
python-dotenv
numpy
```

