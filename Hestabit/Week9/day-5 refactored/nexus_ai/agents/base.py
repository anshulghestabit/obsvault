from __future__ import annotations

import json
import re
from typing import Any

from autogen_core import RoutedAgent
from autogen_core.models import SystemMessage, UserMessage

from nexus_ai.logger import NexusLogger
from utils.day3_helpers import truncate_text


class NexusBaseAgent(RoutedAgent):
    def __init__(
        self,
        name: str,
        model_client: Any,
        nexus_logger: NexusLogger,
        debug_mode: bool = False,
    ) -> None:
        super().__init__(name)
        self._model_client = model_client
        self._logger = nexus_logger
        self._debug_mode = debug_mode

    def _debug(self, text: str) -> None:
        if self._debug_mode:
            print(text)

    async def _llm_text(self, system_prompt: str, user_prompt: str, max_chars: int = 12000) -> str:
        result = await self._model_client.create(
            [
                SystemMessage(content=system_prompt),
                UserMessage(content=truncate_text(user_prompt, max_chars), source=self.id.type),
            ]
        )
        return str(result.content).strip()

    async def _llm_json(self, system_prompt: str, user_prompt: str, max_chars: int = 12000) -> dict:
        raw = await self._llm_text(system_prompt, user_prompt, max_chars=max_chars)
        cleaned = raw.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return {}