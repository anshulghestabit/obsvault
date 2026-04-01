# Day 4 — Memory System

## Goal

Implement a memory-aware local AutoGen assistant with:

- Short-term memory (session window)
- Long-term memory (SQLite)
- Vector recall (FAISS)
- Memory injection into agent context

This matches the Day 4 requirement:

New Query  
→ Search memory  
→ Fetch similar context  
→ Inject in prompt  
→ Generate with context

---

## Files

- `memory/session_memory.py`
- `memory/sqlite_store.py`
- `memory/vector_store.py`
- `orchestrator/memory_orchestrator.py`
- `memory/long_term.db` (auto-created on first run)

---

## Architecture

### 1. Short-term memory
`SessionMemory` keeps the latest N messages in a deque.

Purpose:
- maintain current session continuity
- keep latest exchange visible to the answering agent
- avoid losing immediate local context

### 2. Long-term memory
`SQLiteStore` persists:

- conversation history
- extracted durable facts

Table: `memories`

Kinds:
- `conversation`
- `fact`

Categories:
- `episodic`
- `semantic`
- `preference`
- `constraint`
- `project`

### 3. Vector memory
`FaissSQLiteMemory` stores embeddings for important facts.

Flow:
- facts are embedded with LM Studio `/v1/embeddings`
- vectors are stored in FAISS
- metadata links each vector back to the SQLite row
- retrieval finds the most similar memory rows
- retrieved rows are injected into AutoGen context using `update_context()`

### 4. Orchestrator
`MemoryOrchestrator` coordinates the full cycle:

1. receive user query
2. add to short-term session memory
3. run answer agent
4. AutoGen calls long-term memory `update_context()`
5. retrieved memory is inserted as system context
6. assistant answers
7. user + assistant exchange stored in SQLite
8. fact extractor summarizes durable memory
9. facts embedded and stored in FAISS

---

## Why both SQLite and FAISS?

### SQLite
Used for:
- durable storage
- exact persistence
- readable history
- recovery after restart

### FAISS
Used for:
- similarity search
- retrieval by meaning
- fast recall of semantically related facts

SQLite stores the truth.
FAISS stores the searchable vector index.

---

## Episodic vs Semantic memory

### Episodic
Raw past exchanges.
Example:
- user asked to rebuild Day 4 in a fresh folder

### Semantic
Compressed durable facts.
Example:
- user prefers LM Studio only
- user wants AutoGen-based orchestration
- user needs an orchestrator entrypoint instead of a simple runner

---

## Run

1. Install dependencies from `requirements.txt`
2. Copy `.env.example` to `.env`
3. Put the correct LM Studio chat and embedding model IDs in `.env`
4. Start LM Studio server
5. Run:

```bash
python -m orchestrator.memory_orchestrator