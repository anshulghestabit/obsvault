# RAG Architecture - Day 1 Deliverable

## Overview

This project implements the Day 1 foundation of a Retrieval-Augmented Generation (RAG) pipeline.

The current scope focuses on:

- document ingestion
- text cleaning
- chunk generation
- embedding creation
- FAISS-based semantic retrieval

This is the retrieval backbone of a larger RAG system.

---

## Deliverables Implemented

- `src/pipelines/ingest.py`
- `src/embeddings/embedder.py`
- `src/vectorstore/index.faiss`
- `src/retriever/query_engine.py`
- `RAG-ARCHITECTURE.md`

---

## Pipeline Flow

### 1. Document Ingestion

The ingestion pipeline reads supported files from:

`src/data/raw/`

Supported formats:

- Markdown (`.md`)
- Text (`.txt`)
- PDF (`.pdf`)
- CSV (`.csv`)
- DOCX (`.docx`)

Each document is loaded, normalized, and converted into a common internal structure.

---

### 2. Text Cleaning

Basic normalization is applied to improve chunk quality:

- remove repeated whitespace
- normalize line breaks
- strip empty sections
- preserve meaningful paragraph structure

The goal is to improve retrieval without over-processing the source text.

---

### 3. Chunking Strategy

Documents are split into paragraph-aware chunks.

Current strategy:

- target chunk size: ~600 words
- overlap: ~100 words
- preserve paragraph boundaries when possible
- discard very tiny chunks unless they are the only available content

Each chunk includes metadata such as:

- `chunk_id`
- `source`
- `source_path`
- `doc_type`
- `chunk_index`

This metadata makes retrieval results traceable and debuggable.

---

### 4. Embedding Generation

Chunk embeddings are generated using:

`sentence-transformers/all-MiniLM-L6-v2`

Why this model:

- lightweight
- fast on CPU
- strong enough for Day 1 semantic retrieval
- simple to use for local development

Embeddings are normalized before indexing so that cosine similarity can be approximated using inner product search.

---

### 5. Vector Store

The vector store uses **FAISS**.

Index type:

- `IndexFlatIP`

Why this choice:

- simple
- deterministic
- easy to debug
- well-suited for Day 1 local retrieval

Artifacts produced:

- `src/vectorstore/index.faiss`
- `src/vectorstore/chunk_store.json`

The FAISS index stores vectors.
The metadata file stores chunk text and metadata in the same order as indexed vectors.

---

### 6. Query Retrieval

The query engine performs these steps:

1. load FAISS index
2. load chunk metadata
3. embed the user query
4. search top-k nearest chunks
5. return chunk text with metadata and similarity score

This provides the semantic retrieval stage required for later generator integration.

---

## Design Principles

This implementation follows simple engineering principles aligned with PEP 20:

- explicit is better than implicit
- simple is better than complex
- readability counts
- errors should not pass silently
- practicality beats purity

The code is intentionally modular:

- loaders handle document parsing
- chunker handles text segmentation
- ingest pipeline creates chunk records
- embedder builds vector representations
- query engine performs retrieval

---

## Output Files

### Ingestion Output

- `src/data/cleaned/cleaned_documents.jsonl`
- `src/data/chunks/chunks.jsonl`

### Embedding / Retrieval Output

- `src/vectorstore/index.faiss`
- `src/vectorstore/chunk_store.json`

---

## Example Execution Order

### Step 1: Ingest documents

```bash
python src/pipelines/ingest.py