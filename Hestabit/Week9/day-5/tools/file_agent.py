from __future__ import annotations

import json
import re
from pathlib import Path

from autogen_core import MessageContext, RoutedAgent, message_handler

from models.day3_messages import Day3Task, FileInspection
from utils.day3_helpers import infer_language_from_path, is_code_extension, parse_json


WORKSPACE_DIR = Path("data").resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def file_exists(file_path: str) -> str:
    """Check file existence."""
    path = Path(file_path).resolve()
    return json.dumps(
        {
            "path": str(path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "suffix": path.suffix.lower(),
        },
        indent=2,
    )


def detect_file_type(file_path: str) -> str:
    """Detect file type."""
    path = Path(file_path).resolve()
    suffix = path.suffix.lower()

    if suffix == ".csv":
        file_type = "csv"
    elif suffix in {".db", ".sqlite"}:
        file_type = "sqlite"
    elif suffix in {".txt", ".md", ".json", ".py", ".log", ".yaml", ".yml", ".xml", ".html", ".css", ".js", ".ts"}:
        file_type = "text"
    else:
        file_type = "unknown"

    return json.dumps({"path": str(path), "file_type": file_type}, indent=2)


def read_text_file(file_path: str) -> str:
    """Read a text file."""
    path = Path(file_path).resolve()
    if not path.exists():
        return json.dumps({"error": f"File not found: {path}"}, indent=2)

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return json.dumps({"path": str(path), "content": content}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def write_text_file(file_path: str, content: str) -> str:
    """Write a text file."""
    path = Path(file_path).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return json.dumps({"status": "ok", "path": str(path)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def list_files(directory: str = "data") -> str:
    """List files recursively."""
    base = Path(directory).resolve()
    if not base.exists():
        return json.dumps({"error": f"Directory not found: {base}"}, indent=2)

    files = [str(p) for p in base.rglob("*") if p.is_file()]
    return json.dumps({"files": files, "count": len(files)}, indent=2)


def local_search_files(directory: str, query: str) -> str:
    """Search text in files."""
    base = Path(directory).resolve()
    if not base.exists():
        return json.dumps({"error": f"Directory not found: {base}"}, indent=2)

    matches = []
    query_lower = query.lower()

    for path in base.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            if query_lower in line.lower():
                matches.append(
                    {
                        "file": str(path),
                        "line_no": line_no,
                        "line": line.strip(),
                    }
                )

    return json.dumps({"matches": matches, "count": len(matches)}, indent=2)


class FileAgent(RoutedAgent):
    def __init__(self, name: str, debug_mode: bool = False) -> None:
        super().__init__(name)
        self._debug_mode = debug_mode

    def _debug(self, text: str) -> None:
        if self._debug_mode:
            print(text)

    def _extract_all_paths(self, query: str) -> list[str]:
        return re.findall(r'([A-Za-z0-9_\-./\\]+?\.[A-Za-z0-9]+)', query)

    def _detect_intent(self, query: str, output_path: str = "") -> str:
        q = query.lower()

        code_patterns = [
            "generate code",
            "generate a code",
            "write code",
            "write a code",
            "create code",
            "create a code",
            "implement",
            "create script",
            "write script",
            "build function",
            "write function",
            "generate function",
            "save it in",
            "save it to",
            "save it at",
            "save to",
            "save at",
            "save in",
        ]
        if any(p in q for p in code_patterns):
            return "code_generation"

        if output_path and is_code_extension(output_path):
            code_hints = [
                "code",
                "script",
                "function",
                "class",
                "program",
                "algorithm",
                "binary search",
                "sort",
                "api",
                "backend",
            ]
            if any(h in q for h in code_hints):
                return "code_generation"

        analysis_patterns = [
            "analyze",
            "analyse",
            "insight",
            "insights",
            "summary",
            "statistics",
            "profile dataset",
            "inspect data",
            "find",
            "which",
            "highest",
            "lowest",
        ]
        if any(p in q for p in analysis_patterns):
            return "analysis"

        return "general"

    def _requested_items(self, query: str) -> int:
        match = re.search(r'(\d+)\s+(insight|insights|points|items)', query.lower())
        if match:
            return max(1, int(match.group(1)))
        return 5

    @message_handler
    async def handle_task(self, message: Day3Task, ctx: MessageContext) -> FileInspection:
        self._debug("[file_agent] started")

        paths = self._extract_all_paths(message.query)
        output_path = paths[-1] if paths else ""
        intent = self._detect_intent(message.query, output_path=output_path)
        requested_items = self._requested_items(message.query)

        file_path = ""

        if intent == "code_generation":
            file_type = infer_language_from_path(output_path) if output_path else "python"
            summary = (
                f"Intent: code_generation\n"
                f"Output path: {str(Path(output_path).resolve()) if output_path else 'not provided'}\n"
                f"Language: {file_type}"
            )
            self._debug("[file_agent] finished")
            return FileInspection(
                query=message.query,
                intent=intent,
                file_path="",
                output_path=output_path,
                exists=False,
                file_type=file_type,
                requested_items=requested_items,
                summary=summary,
            )

        if paths:
            file_path = paths[0]
        else:
            files_info = parse_json(list_files("data"))
            files = files_info.get("files", [])
            if files:
                file_path = str(files[0])

        exists_info = parse_json(file_exists(file_path)) if file_path else {"exists": False, "path": ""}
        type_info = parse_json(detect_file_type(file_path)) if file_path else {"file_type": "unknown"}

        exists = bool(exists_info.get("exists", False))
        file_path = str(exists_info.get("path", file_path))
        file_type = str(type_info.get("file_type", "unknown"))

        search_hits = []
        if exists and file_type == "text":
            keywords = message.query.split()[:2]
            if keywords:
                search_hits = parse_json(local_search_files("data", keywords[0])).get("matches", [])[:3]

        summary = (
            f"Intent: {intent}\n"
            f"File path: {file_path or 'not found'}\n"
            f"Exists: {exists}\n"
            f"File type: {file_type}\n"
            f"Requested items: {requested_items}\n"
            f"Local matches found: {len(search_hits)}"
        )

        self._debug("[file_agent] finished")

        return FileInspection(
            query=message.query,
            intent=intent,
            file_path=file_path,
            output_path="",
            exists=exists,
            file_type=file_type,
            requested_items=requested_items,
            summary=summary,
        )