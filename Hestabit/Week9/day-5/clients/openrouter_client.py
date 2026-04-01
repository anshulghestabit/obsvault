from dataclasses import dataclass
from typing import Sequence

import requests


@dataclass
class OpenRouterCreateResult:
    content: str


class OpenRouterChatClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        app_url: str = "http://localhost",
        app_title: str = "week9-day1",
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.app_url = app_url
        self.app_title = app_title
        self.timeout = timeout

    def _messages_to_openrouter(self, messages: Sequence[object]) -> list[dict]:
        converted = []

        for msg in messages:
            content = getattr(msg, "content", "")
            class_name = msg.__class__.__name__.lower()

            if "system" in class_name:
                role = "system"
            elif "assistant" in class_name:
                role = "assistant"
            else:
                role = "user"

            converted.append(
                {
                    "role": role,
                    "content": str(content),
                }
            )

        return converted

    async def create(self, messages: Sequence[object], cancellation_token=None) -> OpenRouterCreateResult:
        payload = {
            "model": self.model,
            "messages": self._messages_to_openrouter(messages),
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.app_url,
                "X-OpenRouter-Title": self.app_title,
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return OpenRouterCreateResult(content=content.strip())

    async def close(self) -> None:
        pass