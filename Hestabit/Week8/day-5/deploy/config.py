from pathlib import Path
import os

try:
    BASE_DIR = Path(__file__).resolve().parent
except OSError as exc:
    raise OSError("failed to resolve config base directory") from exc

# =========================
# Model Path (Docker + Local Safe)
# =========================

try:
    MODEL_PATH = Path(
        os.getenv(
            "MODEL_PATH",
            (BASE_DIR / "../quantized/model.gguf").resolve()
        )
    )
except (TypeError, OSError) as exc:
    raise ValueError("failed to resolve MODEL_PATH configuration") from exc

# =========================
# Generation Defaults
# =========================

MAX_TOKENS = 256
TEMPERATURE = 0.7
TOP_P = 0.9
TOP_K = 40

# =========================
# Context / Chat Settings
# =========================

CONTEXT_WINDOW = 2048

SYSTEM_PROMPT = (
    "You are a medical assistant. "
    "Answer clearly, safely, and accurately. "
    "Do not hallucinate medical facts."
)
