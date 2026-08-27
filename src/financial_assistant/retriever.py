"""Retrieval for the RAG knowledge base.

Implements a simple, dependency-free retrieval that combines:
1. Keyword overlap scoring between the query and each chunk's text.
2. Tag/metadata scoring using each chunk's pre-defined tags.

This mirrors the team's RAG research: start simple (hybrid keyword + metadata),
add embeddings/reranking only if evaluation shows a need. Top-K results are
returned with scores; when no chunk scores above the threshold, retrieval is
reported as empty so the assistant can fall back gracefully (no hallucination).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .knowledge_base import Chunk

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "to", "of", "for", "on",
    "in", "with", "and", "or", "but", "how", "what", "give", "me", "my",
    "i", "can", "do", "does", "it", "at", "from", "by", "this", "that",
}


def _tokens(text: str) -> set:
    words = re.findall(r"[a-z']+", text.lower())
    return {w for w in words if w not in _STOPWORDS}


@dataclass
class RetrievedChunk:
    """A chunk with its retrieval score."""
    chunk: Chunk
    score: float


def _text_score(query_tokens, chunk_text: str) -> float:
    tokens = _tokens(chunk_text)
    if not tokens:
        return 0.0
    hits = len(query_tokens & tokens)
    return (2.0 * hits) / (len(query_tokens) + len(tokens))


def _tag_score(query_tokens, chunk: Chunk) -> float:
    if not chunk.tags:
        return 0.0
    tag_tokens = set()
    for tag in chunk.tags:
        tag_tokens |= _tokens(tag)
    hits = len(query_tokens & tag_tokens)
    return (1.0 * hits) / max(1, len(tag_tokens))


def retrieve(query: str, chunks: List[Chunk], top_k: int = 3,
             min_score: float = 0.10) -> List[RetrievedChunk]:
    """Retrieve the Top-K most relevant chunks for ``query``.

    Final score = text-overlap score + tag-match score. Chunks below
    ``min_score`` are excluded so irrelevant queries return an empty result.
    """
    query_tokens = _tokens(query or "")
    if not query_tokens:
        return []
    scored: List[RetrievedChunk] = []
    for chunk in chunks:
        text_s = _text_score(query_tokens, chunk.text)
        tag_s = _tag_score(query_tokens, chunk)
        score = round(text_s + tag_s, 4)
        if score >= min_score:
            scored.append(RetrievedChunk(chunk=chunk, score=score))
    scored.sort(key=lambda rc: rc.score, reverse=True)
    return scored[:top_k]


def best_chunk(query: str, chunks: List[Chunk]) -> Optional[RetrievedChunk]:
    """Return the single best-matching chunk, or ``None`` if none qualifies."""
    results = retrieve(query, chunks, top_k=1)
    return results[0] if results else None