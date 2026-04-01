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