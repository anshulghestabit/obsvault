import json
import re
from pathlib import Path
from typing import Any, Iterable


def clean_text(text: str) -> str:
    """
    Clean text with conservative normalization.

    The goal is to improve retrieval quality without destroying structure.
    """
    if not text:
        return ""

    text = text.replace("\u00a0", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)

    return text.strip()


def slugify(value: str) -> str:
    """Convert a string into a simple, filesystem-friendly slug."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Write an iterable of dictionaries to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file into a list of dictionaries."""
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows