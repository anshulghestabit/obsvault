import logging
from pathlib import Path

try:
    BASE_DIR = Path(__file__).resolve().parent.parent
except OSError as exc:
    raise OSError("failed to resolve logger base directory") from exc

LOG_DIR = BASE_DIR / "logs"
try:
    LOG_DIR.mkdir(exist_ok=True)
except OSError as exc:
    raise OSError(f"failed to create log directory: {LOG_DIR}") from exc

LOG_FILE = LOG_DIR / "llm_api.log"

logger = logging.getLogger("llm-api")
logger.setLevel(logging.INFO)

if not logger.handlers:
    try:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    except OSError as exc:
        raise OSError(f"failed to initialize log handlers for: {LOG_FILE}") from exc
    except Exception as exc:
        raise RuntimeError("failed to configure application logger") from exc
