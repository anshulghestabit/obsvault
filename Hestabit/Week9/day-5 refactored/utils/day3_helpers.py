import json
from pathlib import Path


def parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def truncate_text(text: str, limit: int = 6000) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def infer_language_from_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
        ".cs": "csharp",
        ".sql": "sql",
        ".sh": "bash",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return mapping.get(suffix, "python")


def is_code_extension(path: str) -> bool:
    return Path(path).suffix.lower() in {
        ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs",
        ".php", ".rb", ".cs", ".sql", ".sh", ".html", ".css",
        ".json", ".xml", ".yaml", ".yml",
    }