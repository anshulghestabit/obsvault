from pathlib import Path

import pandas as pd
from pypdf import PdfReader

try:
    from docx import Document
except ImportError:  # pragma: no cover
    Document = None

from src.utils.helpers import clean_text


def load_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(text)

    return {
        "source": path.name,
        "source_path": str(path),
        "doc_type": "markdown",
        "text": text,
        "pages": None,
    }


def load_text(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(text)

    return {
        "source": path.name,
        "source_path": str(path),
        "doc_type": "text",
        "text": text,
        "pages": None,
    }


def load_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    page_items: list[dict] = []
    page_texts: list[str] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_text = clean_text(page_text)
        page_items.append({"page": page_number, "text": page_text})
        page_texts.append(page_text)

    full_text = clean_text("\n\n".join(page_texts))

    return {
        "source": path.name,
        "source_path": str(path),
        "doc_type": "pdf",
        "text": full_text,
        "pages": page_items,
    }


def load_csv(path: Path) -> dict:
    dataframe = pd.read_csv(path)
    text = dataframe.to_csv(index=False)
    text = clean_text(text)

    return {
        "source": path.name,
        "source_path": str(path),
        "doc_type": "csv",
        "text": text,
        "pages": None,
    }


def load_docx(path: Path) -> dict:
    if Document is None:
        raise ImportError(
            "python-docx is required for DOCX support. Install it with: pip install python-docx"
        )

    document = Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    text = clean_text("\n".join(paragraphs))

    return {
        "source": path.name,
        "source_path": str(path),
        "doc_type": "docx",
        "text": text,
        "pages": None,
    }


def load_document(path: Path) -> dict:
    """
    Dispatch loader by file extension.
    """
    suffix = path.suffix.lower()

    if suffix == ".md":
        return load_markdown(path)
    if suffix == ".txt":
        return load_text(path)
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".docx":
        return load_docx(path)

    raise ValueError(f"Unsupported file type: {path.suffix}")