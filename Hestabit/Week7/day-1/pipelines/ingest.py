import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config.settings import (  # noqa: E402
    CHUNKS_FILE,
    CLEANED_DOCS_FILE,
    RAW_DATA_DIR,
    SUPPORTED_EXTENSIONS,
    ensure_directories,
)
from src.utils.chunker import build_chunk_records  # noqa: E402
from src.utils.helpers import clean_text, write_jsonl  # noqa: E402
from src.utils.loaders import load_document  # noqa: E402


def find_source_files(root: Path) -> list[Path]:
    """
    Recursively find supported files under the raw data directory.
    """
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return sorted(files)


def ingest_documents() -> tuple[list[dict], list[dict]]:
    """
    Load raw documents, clean text, build chunks, and return:
    - cleaned document records
    - chunk records
    """
    ensure_directories()

    source_files = find_source_files(RAW_DATA_DIR)
    if not source_files:
        raise FileNotFoundError(
            f"No supported source files found in: {RAW_DATA_DIR}"
        )

    cleaned_documents: list[dict] = []
    all_chunks: list[dict] = []

    for file_path in source_files:
        document = load_document(file_path)
        document["text"] = clean_text(document["text"])

        cleaned_documents.append(
            {
                "source": document["source"],
                "source_path": document["source_path"],
                "doc_type": document["doc_type"],
                "text": document["text"],
            }
        )

        chunks = build_chunk_records(document)
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("Ingestion completed but produced no chunks.")

    return cleaned_documents, all_chunks


def main() -> None:
    cleaned_documents, all_chunks = ingest_documents()

    write_jsonl(CLEANED_DOCS_FILE, cleaned_documents)
    write_jsonl(CHUNKS_FILE, all_chunks)

    print(f"[OK] Cleaned documents saved to: {CLEANED_DOCS_FILE}")
    print(f"[OK] Chunks saved to: {CHUNKS_FILE}")
    print(f"[INFO] Documents processed: {len(cleaned_documents)}")
    print(f"[INFO] Chunks created: {len(all_chunks)}")


if __name__ == "__main__":
    main()