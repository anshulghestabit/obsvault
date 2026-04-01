import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """
    Simple local-file conversational memory store.

    Stores the last N messages per session.
    """

    def __init__(self, file_path: str | Path, max_messages: int = 5) -> None:
        self.file_path = Path(file_path)
        self.max_messages = max_messages
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        with self.file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save(self, data: dict[str, list[dict[str, Any]]]) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        data = self._load()
        return data.get(session_id, [])

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        data = self._load()

        if session_id not in data:
            data[session_id] = []

        data[session_id].append(
            {
                "role": role,
                "content": content,
            }
        )

        data[session_id] = data[session_id][-self.max_messages :]
        self._save(data)

    def clear_session(self, session_id: str) -> None:
        data = self._load()
        data.pop(session_id, None)
        self._save(data)