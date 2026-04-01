from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

DATA_DIR = SRC_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
CHUNKS_DIR = DATA_DIR / "chunks"

VECTORSTORE_DIR = SRC_DIR / "vectorstore"
LOGS_DIR = SRC_DIR / "logs"

CHUNKS_FILE = CHUNKS_DIR / "chunks.jsonl"
CLEANED_DOCS_FILE = CLEANED_DATA_DIR / "cleaned_documents.jsonl"

FAISS_INDEX_FILE = VECTORSTORE_DIR / "index.faiss"
VECTOR_METADATA_FILE = VECTORSTORE_DIR / "chunk_store.json"

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# BGE v1.5: documents do not need instruction.
# Short retrieval queries can benefit from this prefix.
QUERY_INSTRUCTION_PREFIX = "Represent this sentence for searching relevant passages: "

# CPU-friendly batching
EMBEDDING_BATCH_SIZE = 16

# Word-based approximation for a 512-token embedding model
CHUNK_SIZE_WORDS = 230
CHUNK_OVERLAP_WORDS = 40
MIN_CHUNK_WORDS = 60

TOP_K = 5

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".csv", ".docx"}


def ensure_directories() -> None:
    """Create required directories if they do not exist."""
    for directory in [
        RAW_DATA_DIR,
        CLEANED_DATA_DIR,
        CHUNKS_DIR,
        VECTORSTORE_DIR,
        LOGS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)