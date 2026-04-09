# Multimodal RAG - Day 3 Deliverable

## Overview

This document explains the Day 3 implementation of an Image-RAG / Multimodal RAG pipeline.

The goal of Day 3 is to extend the text-based RAG system into a multimodal retrieval system that supports:

- image ingestion
- OCR extraction
- image caption generation
- CLIP image embeddings
- multimodal vector indexing
- text-to-image retrieval
- image-to-image retrieval
- image-to-text answer support

---

## Deliverables Implemented

- `src/pipelines/image_ingest.py`
- `src/embeddings/clip_embedder.py`
- `src/retriever/image_search.py`
- `MULTIMODAL-RAG.md`

---

## Supported Inputs

The pipeline supports ingestion of:

- PNG
- JPG / JPEG
- WEBP
- BMP
- scanned PDFs

Raw image files are placed in:

`src/data/raw_images/`

---

## Pipeline Flow

### 1. Image Ingestion

The image ingestion pipeline reads files from:

`src/data/raw_images/`

For regular image files:
- load image
- extract OCR text using Tesseract
- generate a caption using BLIP
- store metadata as JSONL

For scanned PDFs:
- convert pages to PNG images
- process each page independently
- store page-level image records

Output:
- `src/data/image_cleaned/image_documents.jsonl`

---

### 2. OCR Extraction

OCR is performed using Tesseract.

Purpose:
- recover text from scanned forms
- recover labels from diagrams
- support text-based explanation after retrieval

OCR text is stored in each image record and can later be used for grounded answer generation.

---

### 3. Caption Generation

Caption generation is performed using:

- `Salesforce/blip-image-captioning-base`

Purpose:
- summarize visual content
- improve searchability for images with little or no OCR text
- create a human-readable description for retrieval results

Each image record stores:
- `caption`
- `ocr_text`
- `search_text`

---

### 4. CLIP Embedding Generation

Image embeddings are generated using:

- `openai/clip-vit-base-patch32`

Purpose:
- map images and text into a shared vector space
- support text-to-image retrieval
- support image-to-image retrieval

The embedding pipeline:
- reads image metadata
- computes CLIP image embeddings
- normalizes embeddings
- stores them in a FAISS index

Outputs:
- `src/vectorstore/images/image_index.faiss`
- `src/vectorstore/images/image_store.json`

---

## Query Modes

### Text → Image

A text query is embedded using the CLIP text encoder.

The system retrieves the most similar images from the image FAISS index.

Example:
`"engineering wiring diagram"`

---

### Image → Image

A query image is embedded using the CLIP image encoder.

The system retrieves visually similar images from the same vector index.

This supports finding related diagrams, forms, or screenshots.

---

### Image → Text Answer

A query image is first used for image-to-image retrieval.

The system then returns:
- retrieved captions
- OCR excerpts
- source references

This provides a retrieval-backed answer context for image explanation.

---

## Multimodal Vector DB Design

The design follows the same explicit style as Day 1 and Day 2.

### Stored Artifacts
- FAISS image index
- metadata JSON store

### Metadata per image
Each image record contains:
- `image_id`
- `source`
- `file_path`
- `image_type`
- `ocr_text`
- `caption`
- `search_text`
- `metadata`

### Why this design works
- simple
- traceable
- debuggable
- easy to extend later with reranking or multimodal generation

---

## Example Workflow

```text
raw images / scanned PDFs
-> OCR extraction
-> BLIP caption generation
-> CLIP image embedding
-> FAISS image index
-> retrieve by text or image