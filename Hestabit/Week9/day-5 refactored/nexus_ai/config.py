from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env.md")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class NexusSettings:
    model_provider: str

    lmstudio_base_url: str
    lmstudio_api_key: str
    lmstudio_model: str

    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_model: str

    groq_api_key: str
    groq_base_url: str
    groq_model: str

    debug_mode: bool
    log_dir: str
    max_plan_steps: int
    parallel_workers: int
    session_db_path: str
    vector_index_path: str
    vector_metadata_path: str

    def validate(self) -> None:
        allowed_providers = {"lmstudio", "groq", "openrouter"}
        if self.model_provider not in allowed_providers:
            raise ValueError(
                f"MODEL_PROVIDER must be one of {sorted(allowed_providers)}, "
                f"got: {self.model_provider}"
            )

        if self.model_provider == "lmstudio":
            if not self.lmstudio_base_url:
                raise ValueError("LMSTUDIO_BASE_URL is missing.")
            if not self.lmstudio_model:
                raise ValueError("LMSTUDIO_MODEL is missing.")

        if self.model_provider == "groq":
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY is missing.")
            if not self.groq_model:
                raise ValueError("GROQ_MODEL is missing.")

        if self.model_provider == "openrouter":
            if not self.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is missing.")
            if not self.openrouter_model:
                raise ValueError("OPENROUTER_MODEL is missing.")


def get_nexus_settings() -> NexusSettings:
    return NexusSettings(
        model_provider=os.getenv("MODEL_PROVIDER", "lmstudio").strip().lower(),

        lmstudio_base_url=os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1").strip(),
        lmstudio_api_key=os.getenv("LMSTUDIO_API_KEY", "lm-studio").strip(),
        lmstudio_model=os.getenv("LMSTUDIO_MODEL", "").strip(),

        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip(),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free").strip(),

        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip(),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),

        debug_mode=_to_bool(os.getenv("DEBUG_MODE", "false")),
        log_dir=os.getenv("NEXUS_LOG_DIR", "logs"),
        max_plan_steps=int(os.getenv("NEXUS_MAX_PLAN_STEPS", "6")),
        parallel_workers=int(os.getenv("NEXUS_PARALLEL_WORKERS", "3")),
        session_db_path=os.getenv("NEXUS_SESSION_DB", "memory/long_term.db"),
        vector_index_path=os.getenv("NEXUS_VECTOR_INDEX", "memory/vector.index"),
        vector_metadata_path=os.getenv("NEXUS_VECTOR_META", "memory/vector_metadata.pkl"),
    )