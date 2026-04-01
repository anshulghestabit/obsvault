from typing import Any

from src.config.settings import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS, MIN_CHUNK_WORDS
from src.utils.helpers import clean_text, slugify


def split_into_paragraphs(text: str) -> list[str]:
    """
    Split text into paragraphs while preserving useful structure.
    """
    text = clean_text(text)
    if not text:
        return []

    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
    return [paragraph for paragraph in paragraphs if paragraph]


def word_count(text: str) -> int:
    return len(text.split())


def build_chunk_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Chunk a document into paragraph-aware chunks.

    Strategy:
    - Keep chunks near CHUNK_SIZE_WORDS
    - Preserve paragraph boundaries where possible
    - Add overlap using trailing words from the previous chunk
    """
    text = document["text"]
    paragraphs = split_into_paragraphs(text)

    if not paragraphs:
        return []

    source = document["source"]
    source_slug = slugify(source)

    chunks: list[dict[str, Any]] = []
    current_parts: list[str] = []
    current_word_total = 0

    def flush_chunk(chunk_index: int) -> dict[str, Any] | None:
        nonlocal current_parts, current_word_total

        if not current_parts:
            return None

        chunk_text = clean_text("\n\n".join(current_parts))
        if word_count(chunk_text) < MIN_CHUNK_WORDS and chunks:
            return None

        chunk_record = {
            "chunk_id": f"{source_slug}_chunk_{chunk_index}",
            "text": chunk_text,
            "source": source,
            "source_path": document["source_path"],
            "doc_type": document["doc_type"],
            "chunk_index": chunk_index,
            "word_count": word_count(chunk_text),
            "metadata": {
                "source": source,
                "doc_type": document["doc_type"],
            },
        }
        return chunk_record

    for paragraph in paragraphs:
        paragraph_words = paragraph.split()
        paragraph_word_count = len(paragraph_words)

        if current_word_total + paragraph_word_count <= CHUNK_SIZE_WORDS:
            current_parts.append(paragraph)
            current_word_total += paragraph_word_count
            continue

        chunk_record = flush_chunk(len(chunks))
        if chunk_record is not None:
            chunks.append(chunk_record)

        overlap_words: list[str] = []
        if current_parts:
            previous_text = clean_text("\n\n".join(current_parts))
            previous_words = previous_text.split()
            overlap_words = previous_words[-CHUNK_OVERLAP_WORDS:]

        current_parts = []
        current_word_total = 0

        if overlap_words:
            overlap_text = " ".join(overlap_words)
            current_parts.append(overlap_text)
            current_word_total += len(overlap_words)

        current_parts.append(paragraph)
        current_word_total += paragraph_word_count

    final_chunk = flush_chunk(len(chunks))
    if final_chunk is not None:
        chunks.append(final_chunk)

    return chunks