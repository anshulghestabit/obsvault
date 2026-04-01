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