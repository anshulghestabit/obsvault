from pathlib import Path
import pandas as pd


def read_text_file(file_path: str) -> str:
    """Read a UTF-8 text file and return its content."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {file_path}"
    if not path.is_file():
        return f"ERROR: Not a file: {file_path}"
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"ERROR: Could not read file: {exc}"


def write_text_file(file_path: str, content: str) -> str:
    """Write UTF-8 text content to a file. Creates parent folders if needed."""
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"SUCCESS: Wrote text file to {file_path}"
    except Exception as exc:
        return f"ERROR: Could not write file: {exc}"


def read_csv_preview(file_path: str, rows: int = 5) -> str:
    """Read a CSV file and return a small preview with shape and columns."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: CSV not found: {file_path}"
    try:
        df = pd.read_csv(path)
        preview = df.head(rows).to_string(index=False)
        return (
            f"CSV_PATH: {file_path}\n"
            f"ROWS: {len(df)}\n"
            f"COLUMNS: {list(df.columns)}\n"
            f"PREVIEW:\n{preview}"
        )
    except Exception as exc:
        return f"ERROR: Could not read CSV: {exc}"


def list_files_in_directory(directory_path: str = ".") -> str:
    """List files and folders inside a directory."""
    path = Path(directory_path)
    if not path.exists():
        return f"ERROR: Directory not found: {directory_path}"
    if not path.is_dir():
        return f"ERROR: Not a directory: {directory_path}"
    items = sorted([p.name for p in path.iterdir()])
    return "\n".join(items) if items else "Directory is empty."
