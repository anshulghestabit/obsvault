from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer


@dataclass
class VectorMemoryItem:
    text: str
    metadata: dict


class FaissVectorStore:
    def __init__(
        self,
        index_path: str = "memory/vector.index",
        metadata_path: str = "memory/vector_metadata.pkl",
        dim: int = 1024,
    ) -> None:
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self.dim = dim
        self.vectorizer = HashingVectorizer(
            n_features=self.dim,
            alternate_sign=False,
            norm="l2",
        )

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = faiss.IndexFlatIP(self.dim)

        if self.metadata_path.exists():
            with open(self.metadata_path, "rb") as f:
                self.items: list[VectorMemoryItem] = pickle.load(f)
        else:
            self.items = []

    def _embed(self, texts: list[str]) -> np.ndarray:
        matrix = self.vectorizer.transform(texts)
        dense = matrix.toarray().astype("float32")
        return dense

    def add_text(self, text: str, metadata: dict | None = None) -> None:
        metadata = metadata or {}
        vector = self._embed([text])
        self.index.add(vector)
        self.items.append(VectorMemoryItem(text=text, metadata=metadata))
        self.save()

    def search(self, query: str, k: int = 3) -> list[dict]:
        if not self.items or self.index.ntotal == 0:
            return []

        query_vector = self._embed([query])
        scores, indices = self.index.search(query_vector, min(k, len(self.items)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            item = self.items[idx]
            results.append(
                {
                    "text": item.text,
                    "metadata": item.metadata,
                    "score": float(score),
                }
            )
        return results

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.items, f)

    def clear(self) -> None:
        self.index = faiss.IndexFlatIP(self.dim)
        self.items = []
        self.save()

    def format_search_results(self, results: list[dict]) -> str:
        if not results:
            return "No similar vector memories found."

        lines = []
        for idx, item in enumerate(results, start=1):
            text = item["text"]
            meta = json.dumps(item["metadata"], ensure_ascii=False)
            score = round(item["score"], 4)
            lines.append(f"{idx}. score={score} | {text} | metadata={meta}")
        return "\n".join(lines)