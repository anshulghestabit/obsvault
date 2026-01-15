# WEEK 7 — GENAI & MULTIMODAL RAG ENGINEERING
(Text RAG + Image RAG + SQL Question Answering + Hybrid Retrieval + Local LLMs)

### USE CASE: Enterprise Knowledge Intelligence System
Interns will build an enterprise-grade GenAI system that can:
* Answer questions from internal documents
* Retrieve & reason over images
* Query structured data using natural language → SQL

### OBJECTIVES
* RAG architecture
* Local LLM setup or API integration
* Hybrid retrieval
* Multimodal embeddings
* SQL-based QA

---

# DAY 1 — LOCAL RAG SYSTEM + PIPELINE ARCHITECTURE

### Learning Outcomes
* RAG architecture
* Local LLM inference
* Embedding generation
* Document chunking

### Mandatory Folder Structure
```text
src/
  data/
  embeddings/
  vectorstore/
  retriever/
  generator/
  pipelines/
  prompts/
  models/
  evaluation/
  utils/
```

### Exercise
Build a local ingestion & chunking pipeline:
* Load PDFs/TXT/CSV
* Clean & Chunk
* Generate embeddings
* Store in Vector DB (FAISS/Qdrant)

### Deliverables
* `/pipelines/ingest.py`
* `/embeddings/embedder.py`
* `/vectorstore/index.faiss`
* `RAG-ARCHITECTURE.md`
