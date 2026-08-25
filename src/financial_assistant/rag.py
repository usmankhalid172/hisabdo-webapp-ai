"""RAG (Retrieval-Augmented Generation) connection layer.

Day 16 deliverable: a minimal, dependency-injection-friendly retriever
interface so the assistant engine can retrieve relevant knowledge-base chunks
or transactions for a question without being coupled to a specific backend.

The engine defaults to :class:`KeywordRetriever` (deterministic, no external
deps). When an embedding provider is configured, :class:`VectorRetriever` can be
used instead via ``FinancialAssistant(retriever=...)``.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Sequence

from .knowledge_base import Chunk


@dataclass
class RetrievedChunk:
    """A chunk returned by a retriever, with its similarity score."""
    chunk: Chunk
    score: float


class BaseRetriever(ABC):
    """Abstract retriever interface."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        """Return the ``top_k`` chunks most relevant to ``query``."""

    def search(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        """Public alias for :meth:`retrieve`."""
        return self.retrieve(query, top_k=top_k)


class KeywordRetriever(BaseRetriever):
    """Simple term-overlap retriever over chunk ``text`` and ``title``."""

    def __init__(self, chunks: Sequence[Chunk]):
        self.chunks = list(chunks)
        # Pre-tokenise for speed; tokens are lowercased words.
        self._tokens = [self._tokenise(c.text + " " + c.title) for c in self.chunks]

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        return [t for t in text.lower().split() if t.isalnum()]

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        if not self.chunks:
            return []
        q_tokens = set(self._tokenise(query))
        if not q_tokens:
            return [RetrievedChunk(c, 0.0) for c in self.chunks[:top_k]]
        scored: List[RetrievedChunk] = []
        for chunk, tokens in zip(self.chunks, self._tokens):
            doc_tokens = set(tokens)
            intersection = q_tokens & doc_tokens
            union = q_tokens | doc_tokens
            score = len(intersection) / len(union) if union else 0.0
            scored.append(RetrievedChunk(chunk, round(score, 4)))
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# Embedding function type: list[str] -> list[list[float]].
EmbedFn = "EmbedFn"


class VectorRetriever(BaseRetriever):
    """Embedding-based retriever using an injected embedding function.

    Parameters
    ----------
    chunks:
        Knowledge-base chunks to search.
    embed:
        Callable ``embed(texts) -> embeddings`` (e.g. an OpenAI embedding
        function). Kept as a plain callable to avoid a hard runtime
        dependency on the OpenAI client here.
    """

    def __init__(self, chunks: Sequence[Chunk], embed):
        self.chunks = list(chunks)
        self.embed = embed
        self._embeddings = self.embed([c.text for c in self.chunks]) \
            if self.chunks else []

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        if not self.chunks:
            return []
        q_emb = self.embed([query])[0]
        scored = [RetrievedChunk(c, round(_cosine(q_emb, e), 4))
                  for c, e in zip(self.chunks, self._embeddings)]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


def build_default_retriever(chunks: Sequence[Chunk]) -> BaseRetriever:
    """Construct the default retriever (keyword-based) for a chunk list."""
    return KeywordRetriever(chunks)
