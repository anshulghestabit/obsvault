# Week 7 - Day 2 Demo

## Title
**Advanced Retrieval and Context Engineering - Day 2 Demo**

---

## Objective
Build an advanced retriever that improves retrieval precision and reduces hallucination by adding:

- hybrid retrieval
- keyword fallback
- reranking
- chunk deduplication
- MMR-based context selection
- fully traceable context sources

---

## Deliverables Completed

- `src/retriever/hybrid_retriever.py`
- `src/retriever/reranker.py`
- `src/pipelines/context_builder.py`
- `RETRIEVAL-STRATEGIES.md`

---

## Day 2 Goals
The Day 2 system extends the Day 1 FAISS-based retriever by adding:

- semantic + keyword hybrid search
- metadata filtering
- reranking
- deduplication
- diversified context selection
- traceable context assembly

---
Day 2 Retrieval Workflow
1. Hybrid Retrieval

The hybrid retriever combines:

Semantic search using FAISS and sentence embeddings

Keyword search using BM25

This improves retrieval quality because:

semantic search captures meaning

keyword search captures exact terms

both methods together increase robustness

2. Metadata Filtering

The retriever supports filters such as:

filters = {"year": "2024", "type": "policy"}

This helps narrow retrieval to more relevant chunks.

3. Reranking

Candidate chunks returned by hybrid retrieval are reranked using query-to-chunk similarity.

This improves:

precision

relevance of final top-k results

4. Deduplication

Deduplication is applied using:

chunk_id

near-text similarity

This reduces repeated context and improves context quality.

5. MMR-based Selection

Max Marginal Relevance (MMR) is used to balance:

relevance

diversity

This avoids stuffing the final context with repetitive chunks.

6. Context Building

The context builder:

retrieves hybrid candidates

reranks them

deduplicates them

assembles final traceable context

The final context contains:

selected chunks

source file names

chunk ids

scores

metadata

This makes the system fully traceable.

Commands Used
Run hybrid retriever
python src/retriever/hybrid_retriever.py --query "annual report strategy" --top-k 5
python src/retriever/hybrid_retriever.py --query "annual report strategy" --top-k 5 --filters '{"year":"2022","type":"report"}'
python src/retriever/hybrid_retriever.py --query "Explain how credit underwriting works" --top-k 5 --filters '{"year":"2024","type":"policy"}'
Run reranker
python src/retriever/reranker.py --query "annual report strategy" --top-k 5
Run context builder
python src/pipelines/context_builder.py --query "annual report strategy" --top-k 5
python src/pipelines/context_builder.py --query "annual report strategy" --top-k 5 --filters '{"year":"2022","type":"report"}'
python src/pipelines/context_builder.py --query "Explain how credit underwriting works" --top-k 5 --filters '{"year":"2024","type":"policy"}'
Output Files Saved for Demo
python src/retriever/hybrid_retriever.py --query "annual report strategy" --top-k 5 > day2_hybrid_output.txt
python src/retriever/reranker.py --query "annual report strategy" --top-k 5 > day2_reranker_output.txt
python src/pipelines/context_builder.py --query "annual report strategy" --top-k 5 > day2_context_output.txt

These files were used as proof of successful execution.

Deliverable Verification
ls -lh src/retriever/hybrid_retriever.py
ls -lh src/retriever/reranker.py
ls -lh src/pipelines/context_builder.py
ls -lh RETRIEVAL-STRATEGIES.md
Features Achieved

semantic retrieval

BM25 keyword retrieval

hybrid search

metadata filtering

keyword fallback

reranking

exact and near-duplicate removal

MMR-based final context selection

traceable context output

Observations

The system works correctly on the available corpus.

Generic or unrelated queries may return noisy results if the dataset does not strongly contain that topic.

Corpus-aligned queries produce more meaningful results.

The retrieval layer is now stronger and more traceable than the Day 1 baseline.
## Dataset Used

**Enterprise RAG Markdown Dataset**  
Source: Kaggle  
Dataset name: `rrr3try/enterprise-rag-markdown`

The dataset was downloaded into `src/data/raw/` and excluded from git using `.gitignore`.

Day 2 uses the Day 1 outputs:
- `src/data/chunks/chunks.jsonl`
- `src/vectorstore/index.faiss`
- `src/vectorstore/chunk_store.json`

---

## Project Structure

```bash
.
├── Demo.md
├── RAG-ARCHITECTURE.md
├── RETRIEVAL-STRATEGIES.md
├── requirements.txt
├── src
│   ├── config
│   │   └── settings.py
│   ├── data
│   │   ├── chunks
│   │   ├── cleaned
│   │   └── raw
│   ├── embeddings
│   │   └── embedder.py
│   ├── pipelines
│   │   ├── context_builder.py
│   │   └── ingest.py
│   ├── retriever
│   │   ├── hybrid_retriever.py
│   │   ├── query_engine.py
│   │   └── reranker.py
│   ├── utils
│   │   ├── chunker.py
│   │   ├── helpers.py
│   │   └── loaders.py
│   └── vectorstore
