from __future__ import annotations

import json
import os
import re
from pathlib import Path

from memory.session_memory import SessionMemory
from memory.vector_store import FaissVectorStore
from tools.file_agent import list_files


_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def parse_json(text: str) -> dict:
    if isinstance(text, dict):
        return text
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def parse_list_files() -> list[str]:
    try:
        data = json.loads(list_files("."))
        return data.get("files", [])
    except Exception:
        return []


def normalize_path_text(path: str) -> str:
    return path.replace("\\", "/").strip().lower()


def _normalize_query_for_paths(query: str) -> str:
    q = query.replace("\\", "/")
    q = q.replace("ouput/", "output/")
    q = q.replace("otput/", "output/")
    q = q.replace("outpt/", "output/")
    return q


def _slugify(text: str, max_len: int = 64) -> str:
    text = text.lower()
    text = re.sub(r"[<>]", " ", text)
    text = re.sub(
        r"\b(save|saved|saving|in|to|at|as|write|the|whole|file|output|markdown|report|document|folder|newly|created|naming)\b",
        " ",
        text,
    )
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return (text or "nexus_output")[:max_len].rstrip("_")


def _trim_segment(segment: str, max_len: int) -> str:
    if len(segment) <= max_len:
        return segment
    stem, suffix = os.path.splitext(segment)
    if suffix:
        allowed = max(8, max_len - len(suffix))
        return stem[:allowed] + suffix
    return segment[:max_len]


def ensure_safe_output_path(path_str: str) -> str:
    path = Path(path_str)
    cleaned_parts: list[str] = []

    for idx, part in enumerate(path.parts):
        if idx == 0 and part in {"/", "\\"}:
            cleaned_parts.append(part)
            continue
        max_len = 72 if idx == len(path.parts) - 1 else 40
        cleaned_parts.append(_trim_segment(part, max_len))

    if path.is_absolute():
        safe = Path(cleaned_parts[0])
        for part in cleaned_parts[1:]:
            safe /= part
    else:
        safe = Path(cleaned_parts[0]) if cleaned_parts else Path()
        for part in cleaned_parts[1:]:
            safe /= part

    return str(safe.resolve())


def request_wants_file_output(query: str) -> bool:
    q = _normalize_query_for_paths(query).lower()
    has_save_intent = any(k in q for k in ["save", "write to", "store in", "output/", "launchpad/"])
    has_file_hint = any(ext in q for ext in [".md", ".txt", ".json", ".py", ".csv", ".yaml", ".yml"])
    return has_save_intent or has_file_hint


def choose_target_file_from_query(query: str) -> str:
    q = _normalize_query_for_paths(query)
    paths = re.findall(r'([A-Za-z0-9_\-./\\]+\.[A-Za-z0-9]+)', q)

    for candidate in paths:
        requested = normalize_path_text(candidate)
        files = parse_list_files()

        exact = [f for f in files if normalize_path_text(f).endswith(requested)]
        if exact:
            return exact[0]

        base = Path(requested).name
        basename_hits = [f for f in files if Path(normalize_path_text(f)).name == base]
        if basename_hits:
            return basename_hits[0]

    return ""


def _infer_default_extension(query: str) -> str:
    q = query.lower()

    if any(ext in q for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".sql"]):
        for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".sql"]:
            if ext in q:
                return ext

    if any(k in q for k in ["code", "script", "utility", "program", "function", "class", "cli"]):
        return ".py"

    if any(k in q for k in ["json", ".json"]):
        return ".json"

    if any(k in q for k in ["yaml", "yml", ".yaml", ".yml"]):
        return ".yaml"

    # Default all design/plan/report/doc tasks to markdown, not txt.
    if any(
        k in q
        for k in [
            "plan",
            "pipeline",
            "architecture",
            "design",
            "module",
            "report",
            "strategy",
            "roadmap",
            "documentation",
            "readme",
            "guide",
            "rag",
        ]
    ):
        return ".md"

    return ".md"


def choose_output_path_from_query(query: str) -> str:
    q = _normalize_query_for_paths(query)

    m = re.search(r'([A-Za-z0-9_\-./\\]+/)<file>(\.[A-Za-z0-9]+)', q, flags=re.IGNORECASE)
    if m:
        directory = m.group(1)
        extension = m.group(2)
        filename = _slugify(q, 48)
        return ensure_safe_output_path(str(Path(directory) / f"{filename}{extension}"))

    m = re.search(r'([A-Za-z0-9_\-./\\]+/)<([A-Za-z0-9_\-]+)>(\.[A-Za-z0-9]+)', q, flags=re.IGNORECASE)
    if m:
        directory = m.group(1)
        placeholder = m.group(2).lower()
        extension = m.group(3)
        if placeholder in {"file", "name_file", "name-file", "filename"}:
            filename = _slugify(q, 48)
        else:
            filename = _slugify(placeholder, 32)
        return ensure_safe_output_path(str(Path(directory) / f"{filename}{extension}"))

    m = re.search(r'([A-Za-z0-9_\-./\\]+/)<([A-Za-z0-9_\-]+)(\.[A-Za-z0-9]+)>', q, flags=re.IGNORECASE)
    if m:
        directory = m.group(1)
        placeholder = m.group(2).lower()
        extension = m.group(3)
        filename = _slugify(q if placeholder == "file" else placeholder, 48)
        return ensure_safe_output_path(str(Path(directory) / f"{filename}{extension}"))

    # Explicit path without extension: save in output/foo/bar
    m = re.search(r'\b(?:save|write|store).+?\b(?:in|to)\s+([A-Za-z0-9_\-./\\]+/[A-Za-z0-9_\-]+)\b', q, flags=re.IGNORECASE)
    if m:
        base_path = m.group(1).replace("\\", "/")
        ext = _infer_default_extension(q)
        return ensure_safe_output_path(base_path + ext)

    paths = re.findall(r'([A-Za-z0-9_\-./\\]+\.(?:md|txt|json|py|csv|yaml|yml))', q, flags=re.IGNORECASE)
    if paths:
        chosen = paths[-1].replace("\\", "/")
        return ensure_safe_output_path(chosen)

    if request_wants_file_output(q):
        folder_match = re.search(r'\b([A-Za-z0-9_\-]+)/<', q)
        folder = folder_match.group(1) if folder_match else "output"
        ext = _infer_default_extension(q)
        filename = _slugify(q, 48)
        return ensure_safe_output_path(str(Path(folder) / f"{filename}{ext}"))

    return ""


def detect_task_type(query: str) -> str:
    q = _normalize_query_for_paths(query).lower()

    if any(k in q for k in ["debug", "error", "traceback", "fix bug", "bug fix", "exception"]):
        return "debugging"
    if any(k in q for k in ["test", "pytest", "unit test", "integration test"]):
        return "testing"
    if ".csv" in q or ".sqlite" in q or ".db" in q or "analyze" in q or "analyse" in q:
        return "data"
    if any(k in q for k in ["write code", "generate code", "create code", "implement", ".py", "script", "utility"]):
        return "code"
    if any(k in q for k in ["readme", "documentation", "doc", "guide", "module"]):
        return "documentation"
    return "general"


def infer_deliverable_mode(task_type: str, query: str, output_path: str) -> str:
    suffix = Path(output_path).suffix.lower() if output_path else ""

    if suffix in {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".sql"}:
        return "code"
    if task_type in {"code", "debugging", "testing"}:
        return "code"
    if task_type == "data":
        return "data"
    return "document"


def infer_depth_threshold(task_type: str, query: str) -> int:
    q = query.lower()

    if any(k in q for k in ["in depth", "deep", "detailed", "comprehensive", "very detailed"]):
        return 1400
    if task_type in {"documentation", "general"}:
        return 900
    if task_type == "data":
        return 500
    return 300


def extract_count_requirements(query: str) -> dict[str, int]:
    q = query.lower()

    for word, value in _NUMBER_WORDS.items():
        q = re.sub(rf"\b{word}\b", str(value), q)

    matches = re.findall(r"\b(\d+)\s+(weeks?|days?|files?|steps?|sections?|modules?|agents?)\b", q)
    result: dict[str, int] = {}
    for number, unit in matches:
        result[unit.rstrip("s")] = int(number)
    return result


def extract_expected_sections_from_query(query: str) -> list[str]:
    q = query.lower()
    sections: list[str] = []

    if "will have" in q:
        tail = q.split("will have", 1)[1]
        tail = re.split(r"[.:\n]", tail)[0]
        parts = re.split(r",|\band\b", tail)
        for part in parts:
            part = re.sub(r"[^a-z0-9\s\-]", " ", part).strip()
            if 3 <= len(part) <= 40:
                sections.append(part)

    common_terms = [
        "learning objective",
        "concept",
        "topics",
        "exercise",
        "deliverables",
        "overview",
        "implementation",
        "deployment",
        "monitoring",
        "evaluation",
        "tradeoffs",
        "risks",
        "timeline",
        "milestones",
        "summary",
        "outputs",
        "ingestion",
        "chunking",
        "embedding",
        "indexing",
        "retrieval",
        "augmentation",
        "generation",
    ]
    for term in common_terms:
        if term in q and term not in sections:
            sections.append(term)

    cleaned: list[str] = []
    for item in sections:
        item = re.sub(r"\s+", " ", item).strip(" -_")
        if item and item not in cleaned:
            cleaned.append(item)
    return cleaned[:20]


def build_memory_context(query: str, session_memory: SessionMemory, vector_store: FaissVectorStore) -> str:
    fact_hits = session_memory.search_facts(query, limit=5)
    vector_hits = vector_store.search(query, k=3)
    return (
        "Recent session context:\n"
        f"{session_memory.format_recent_context()}\n\n"
        "Long-term facts:\n"
        f"{session_memory.format_fact_results(fact_hits)}\n\n"
        "Vector recall:\n"
        f"{vector_store.format_search_results(vector_hits)}"
    )


def strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    return text


def extract_code_block_or_raw(text: str) -> str:
    fenced = re.findall(r"```(?:python|py|bash|json|yaml|sql)?\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        longest = max(fenced, key=len)
        return longest.strip()
    return strip_markdown_fences(text)