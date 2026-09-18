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

    def query(
        self,
        query_vector: np.ndarray,
        top_k: int,
        relevance_threshold: float,
        diversify: bool = True,
        mmr_lambda: float = 0.5,
    ) -> list[RetrievedChunk]:
        """
        Returns the top_k chunks most relevant to query_vector.

        diversify=True (default) applies Maximal Marginal Relevance: a
        candidate that's near-identical to a chunk already selected gets
        penalized, so results spread across genuinely different content
        instead of returning several copies of the same idea. This
        matters a lot here — several xicteksystems.com "pillar guide"
        pages share a templated intro/CTA paragraph with only the topic
        name swapped in (a content-generation quirk on their end, not
        ours), so without diversification a query can come back with
        e.g. 4 near-duplicate intro paragraphs from 4 different pages,
        all scoring the same to 4 decimal places, instead of 4 chunks
        that actually say different things. mmr_lambda trades relevance
        (1.0) against diversity (0.0); 0.5 balances both.
        """
        if not self.chunks or self._vectors is None or len(self.chunks) == 0:
            return []
        # Vectors are L2-normalized at embed time, so a plain dot product
        # is cosine similarity — no need to re-normalize per query.
        scores = self._vectors @ query_vector

        if not diversify:
            top_idx = np.argsort(-scores)[:top_k]
            return [
                RetrievedChunk(chunk=self.chunks[idx], score=float(scores[idx]))
                for idx in top_idx
                if scores[idx] >= relevance_threshold
            ]

        # Candidate pool: relevant chunks to choose diversely among.
        # Wider than top_k so MMR has room to pick a more varied set
        # instead of being stuck with whatever squeezed into a top_k-sized
        # window; capped so this stays cheap on a low-end machine.
        candidate_idx = np.where(scores >= relevance_threshold)[0]
        if len(candidate_idx) == 0:
            return []
        candidate_idx = candidate_idx[np.argsort(-scores[candidate_idx])]
        pool_size = min(len(candidate_idx), max(top_k * 8, 30))
        candidate_idx = candidate_idx[:pool_size]

        selected: list[int] = []
        remaining = list(candidate_idx)
        while remaining and len(selected) < top_k:
            if not selected:
                # First pick is just the most relevant candidate.
                best = remaining[0]
            else:
                selected_vectors = self._vectors[selected]  # (k, dim)
                best = None
                best_mmr = -np.inf
                for idx in remaining:
                    relevance = float(scores[idx])
                    # Redundancy: highest similarity to anything already
                    # picked (dot product of two normalized vectors).
                    redundancy = float(np.max(selected_vectors @ self._vectors[idx]))
                    mmr = mmr_lambda * relevance - (1 - mmr_lambda) * redundancy
                    if mmr > best_mmr:
                        best_mmr = mmr
                        best = idx
            selected.append(best)
            remaining.remove(best)

        return [RetrievedChunk(chunk=self.chunks[idx], score=float(scores[idx])) for idx in selected]

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
