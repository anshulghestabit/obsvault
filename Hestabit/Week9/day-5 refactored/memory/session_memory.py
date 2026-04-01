from __future__ import annotations

import sqlite3
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque


@dataclass
class ConversationTurn:
    role: str
    content: str


@dataclass
class FactRecord:
    fact: str
    category: str
    source: str


class SessionMemory:
    def __init__(self, db_path: str = "memory/long_term.db", max_turns: int = 10) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_turns = max_turns
        self.turns: Deque[ConversationTurn] = deque(maxlen=max_turns)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()
        conn.close()

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append(ConversationTurn(role=role, content=content))

        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO conversations (role, content) VALUES (?, ?)",
            (role, content),
        )
        conn.commit()
        conn.close()

    def get_recent_context(self) -> list[ConversationTurn]:
        return list(self.turns)

    def format_recent_context(self) -> str:
        if not self.turns:
            return "No recent session context."

        lines = []
        for turn in self.turns:
            lines.append(f"{turn.role.upper()}: {turn.content}")
        return "\n".join(lines)

    def extract_important_facts(self, text: str) -> list[FactRecord]:
        facts: list[FactRecord] = []
        lowered = text.lower()

        preference_patterns = [
            ("preference", "prefers"),
            ("preference", "likes"),
            ("preference", "wants"),
            ("preference", "needs"),
            ("constraint", "must"),
            ("constraint", "should"),
            ("identity", "i am"),
            ("identity", "my name is"),
            ("project", "project"),
            ("task", "working on"),
        ]

        for category, marker in preference_patterns:
            if marker in lowered:
                facts.append(FactRecord(fact=text.strip(), category=category, source="session"))
                break

        if not facts and len(text.split()) <= 20:
            facts.append(FactRecord(fact=text.strip(), category="note", source="session"))

        deduped = []
        seen = set()
        for fact in facts:
            key = (fact.fact, fact.category)
            if key not in seen:
                seen.add(key)
                deduped.append(fact)

        return deduped

    def store_facts(self, facts: list[FactRecord]) -> None:
        if not facts:
            return

        conn = self._connect()
        cur = conn.cursor()

        for fact in facts:
            cur.execute(
                "INSERT INTO facts (fact, category, source) VALUES (?, ?, ?)",
                (fact.fact, fact.category, fact.source),
            )

        conn.commit()
        conn.close()

    def search_facts(self, query: str, limit: int = 5) -> list[FactRecord]:
        tokens = [token.strip() for token in query.lower().split() if len(token.strip()) > 2]
        if not tokens:
            return []

        conn = self._connect()
        cur = conn.cursor()

        clauses = " OR ".join(["LOWER(fact) LIKE ?"] * len(tokens))
        values = [f"%{token}%" for token in tokens]
        sql = f"""
            SELECT fact, category, source
            FROM facts
            WHERE {clauses}
            ORDER BY id DESC
            LIMIT ?
        """
        cur.execute(sql, (*values, limit))
        rows = cur.fetchall()
        conn.close()

        return [FactRecord(fact=row[0], category=row[1], source=row[2]) for row in rows]

    def format_fact_results(self, facts: list[FactRecord]) -> str:
        if not facts:
            return "No matching long-term facts."

        lines = []
        for idx, fact in enumerate(facts, start=1):
            lines.append(f"{idx}. [{fact.category}] {fact.fact}")
        return "\n".join(lines)