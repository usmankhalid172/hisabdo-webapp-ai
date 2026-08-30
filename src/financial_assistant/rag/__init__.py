"""Public RAG interfaces for the HisabDo AI Financial Assistant."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Sequence

from ..knowledge_base import Chunk
from .retriever import FaqRetriever, get_retriever


@dataclass
class RetrievedChunk:
    """A chunk returned by a retriever, with its similarity score."""
    chunk: Chunk
    score: float


class BaseRetriever(ABC):
    """Abstract retriever interface."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        """Return the top-k chunks most relevant to the query."""

    def search(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        """Public alias for retrieve."""
        return self.retrieve(query, top_k=top_k)


class KeywordRetriever(BaseRetriever):
    """Simple deterministic term-overlap retriever."""

    def __init__(self, chunks: Sequence[Chunk]):
        self.chunks = list(chunks)
        self._tokens = [
            self._tokenise(c.text + " " + c.title)
            for c in self.chunks
        ]

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        return [t for t in text.lower().split() if t.isalnum()]

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        if not self.chunks:
            return []

        q_tokens = set(self._tokenise(query))

        if not q_tokens:
            return [
                RetrievedChunk(c, 0.0)
                for c in self.chunks[:top_k]
            ]

        scored: List[RetrievedChunk] = []

        for chunk, tokens in zip(self.chunks, self._tokens):
            doc_tokens = set(tokens)
            intersection = q_tokens & doc_tokens
            union = q_tokens | doc_tokens

            score = (
                len(intersection) / len(union)
                if union else 0.0
            )

            scored.append(
                RetrievedChunk(chunk, round(score, 4))
            )

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


class VectorRetriever(BaseRetriever):
    """Embedding-based retriever using an injected embedding function."""

    def __init__(self, chunks: Sequence[Chunk], embed):
        self.chunks = list(chunks)
        self.embed = embed

        self._embeddings = (
            self.embed([c.text for c in self.chunks])
            if self.chunks else []
        )

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        if not self.chunks:
            return []

        q_emb = self.embed([query])[0]

        scored = [
            RetrievedChunk(
                c,
                round(_cosine(q_emb, e), 4)
            )
            for c, e in zip(self.chunks, self._embeddings)
        ]

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


def build_default_retriever(
    chunks: Sequence[Chunk],
) -> BaseRetriever:
    """Construct the deterministic default retriever."""
    return KeywordRetriever(chunks)


__all__ = [
    "FaqRetriever",
    "get_retriever",
    "BaseRetriever",
    "KeywordRetriever",
    "RetrievedChunk",
    "VectorRetriever",
    "build_default_retriever",
]
