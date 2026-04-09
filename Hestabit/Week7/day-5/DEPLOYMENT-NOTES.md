# Day 5 - Deployment Notes

## Overview

This Day 5 capstone wraps the Week 7 systems into a lightweight production-style API.

Implemented deliverables:

- `src/deployment/app.py`
- `src/evaluation/rag_eval.py`
- `src/memory/memory_store.py`
- `CHAT-LOGS.json`
- `Readme/Day-5/DEPLOYMENT-NOTES.md`

---

## Endpoints

### `/ask`
Text RAG endpoint.

Uses:
- Day 2 retrieval pipeline
- context builder
- local memory
- evaluation layer

### `/ask-image`
Image RAG endpoint.

Supports:
- `text-to-image`
- `image-to-image`
- `image-to-text`

Uses:
- Day 3 image retrieval
- OCR text
- captions
- local memory
- evaluation layer

### `/ask-sql`
SQL QA endpoint.

Uses:
- Day 4 SQL pipeline
- local memory
- evaluation layer

---

## Added Capstone Features

### Memory for last 5 messages
Implemented via:
- `src/memory/memory_store.py`

Stores per-session conversation messages in a local JSON-backed structure.

### Refinement loop
Implemented in `app.py`.

If hallucination is detected or confidence is low, the answer is softened with a refinement note.

### Hallucination detection
Implemented via:
- `src/evaluation/rag_eval.py`

Uses lightweight faithfulness/context-overlap scoring.

### Confidence score
Computed in:
- `src/evaluation/rag_eval.py`

Combines faithfulness and retrieval evidence.

### Logging and debugging traces
Implemented through:
- `CHAT-LOGS.json`

Each endpoint appends structured request/response logs.

---

## Architecture

The Day 5 API combines prior days:

- Day 2 → advanced text retrieval
- Day 3 → image retrieval
- Day 4 → SQL question answering
- Day 5 → memory + evaluation + deployment wrapper

---

## Files

### `src/deployment/app.py`
Main FastAPI application.

### `src/evaluation/rag_eval.py`
RAG evaluation helpers:
- context match score
- faithfulness score
- hallucination detection
- confidence score

### `src/memory/memory_store.py`
Stores session-based memory for the last five messages.

### `CHAT-LOGS.json`
Stores endpoint logs in JSON format.

---

## Notes

This implementation is intentionally lightweight and local-first.

It is designed to:
- match the Week 7 capstone deliverables
- stay easy to debug
- remain compatible with your earlier Day 1–4 files

---

## Future Improvements

Possible next upgrades:
- Redis-backed memory
- vector memory store
- better answer generation with a real LLM
- stronger hallucination detection
- Streamlit UI
- Docker deployment
- auth and rate limiting

---

## Outcome

This Day 5 deliverable provides a complete capstone-style wrapper over the Week 7 systems with:

- API structure
- memory
- evaluation
- logging
- refinement loop