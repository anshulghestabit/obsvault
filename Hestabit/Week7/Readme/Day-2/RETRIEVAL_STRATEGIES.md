# Retrieval Strategies - Day 2 Deliverable

## Overview

This document explains the Day 2 retrieval improvements added to the RAG system.

The Day 1 pipeline established:
- document ingestion
- chunking
- embedding generation
- FAISS-based semantic retrieval

Day 2 improves retrieval quality by adding:
- hybrid retrieval
- keyword fallback
- reranking
- chunk deduplication
- context traceability
- context diversification

These additions help improve precision and reduce hallucination in downstream LLM responses.

---

## Deliverables Implemented

- `src/retriever/hybrid_retriever.py`
- `src/retriever/reranker.py`
- `src/pipelines/context_builder.py`
- `RETRIEVAL-STRATEGIES.md`

---

## 1. Hybrid Retrieval

### Semantic Retrieval
Semantic retrieval uses:
- sentence embeddings
- FAISS vector search

This captures meaning-based similarity between the query and document chunks.

Example:
A query such as  
`Explain how credit underwriting works`  
may retrieve chunks that discuss loan approval logic even if they do not use the exact same words.

### Keyword Retrieval
Keyword retrieval uses:
- BM25 ranking

This captures lexical overlap and exact-term matching.

This is useful when:
- the query contains specific keywords
- terminology matters
- the semantic retriever misses exact phrase matches

### Why Hybrid Retrieval
Hybrid retrieval combines semantic and keyword retrieval so that:
- semantic search provides meaning-based recall
- BM25 provides exact-match precision
- retrieval becomes more robust on noisy corpora

This reduces dependence on a single retrieval strategy.

---

## 2. Keyword Fallback

A fallback mechanism is included so that if semantic retrieval is weak or filters become too restrictive, keyword-based candidates still provide usable context.

This improves robustness for:
- rare terms
- highly specific expressions
- documents with noisy structure
- broad mixed corpora

---

## 3. Metadata Filtering

The retriever supports optional metadata filters such as:

```python
filters = {"year": "2024", "type": "policy"}