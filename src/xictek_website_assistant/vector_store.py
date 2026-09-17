"""
Lean local vector store: numpy array of L2-normalized embeddings +
a parallel JSON file of chunk metadata (text/title/url). No vector DB
dependency — per the plan, this is the right scale for a few hundred
website/blog chunks, and it keeps the module dependency-light and
easy to demo (two flat files, easy to inspect, easy to re-ingest).

Persisted layout under `config.index_dir`:
    embeddings.npy   — float32 array, shape (n_chunks, embedding_dim)
    chunks.json      — list of {id, title, url, text}, same order as the rows above

Swapping this for a real vector DB later means replacing this file's
internals only (build/query/save/load) — `service.py` and `router.py`
only ever see `retrieve()`'s return shape, same as the HisabDo
financial_assistant's vector_store.py -> rag_pipeline.ContextChunk pattern.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from .config import get_xictek_settings

EMBEDDINGS_FILENAME = "embeddings.npy"
CHUNKS_FILENAME = "chunks.json"


@dataclass
class Chunk:
    chunk_id: str
    title: str
    text: str
    url: Optional[str] = None


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass
class VectorStore:
    chunks: list[Chunk] = field(default_factory=list)
    _vectors: Optional[np.ndarray] = None  # (n, dim), L2-normalized

    def __len__(self) -> int:
        return len(self.chunks)

    def build(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        if len(chunks) != vectors.shape[0]:
            raise ValueError(
                f"chunk/vector count mismatch: {len(chunks)} chunks vs {vectors.shape[0]} vectors"
            )
        self.chunks = chunks
        self._vectors = vectors

    def query(self, query_vector: np.ndarray, top_k: int, relevance_threshold: float) -> list[RetrievedChunk]:
        if not self.chunks or self._vectors is None or len(self.chunks) == 0:
            return []
        # Vectors are L2-normalized at embed time, so a plain dot product
        # is cosine similarity — no need to re-normalize per query.
        scores = self._vectors @ query_vector
        top_idx = np.argsort(-scores)[:top_k]
        results = []
        for idx in top_idx:
            score = float(scores[idx])
            if score >= relevance_threshold:
                results.append(RetrievedChunk(chunk=self.chunks[idx], score=score))
        return results

    def save(self, index_dir: Optional[Path] = None) -> None:
        index_dir = index_dir or get_xictek_settings().index_dir
        index_dir.mkdir(parents=True, exist_ok=True)
        if self._vectors is None:
            raise ValueError("Cannot save an empty/unbuilt vector store")
        np.save(index_dir / EMBEDDINGS_FILENAME, self._vectors)
        payload = [
            {"id": c.chunk_id, "title": c.title, "url": c.url, "text": c.text}
            for c in self.chunks
        ]
        (index_dir / CHUNKS_FILENAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, index_dir: Optional[Path] = None) -> "VectorStore":
        index_dir = index_dir or get_xictek_settings().index_dir
        vectors_path = index_dir / EMBEDDINGS_FILENAME
        chunks_path = index_dir / CHUNKS_FILENAME
        if not vectors_path.exists() or not chunks_path.exists():
            return cls()  # empty store — caller decides how to handle "no index yet"

        vectors = np.load(vectors_path)
        raw_chunks = json.loads(chunks_path.read_text())
        chunks = [
            Chunk(chunk_id=c["id"], title=c["title"], url=c.get("url"), text=c["text"])
            for c in raw_chunks
        ]
        store = cls()
        store.build(chunks, vectors)
        return store
