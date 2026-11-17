"""Embeddings: turn text into a vector so that texts with similar MEANING are close together.

"kharcha kaise likhun?" and "How do I record an expense?" share no words, so
keyword matching scores them 0. Their embedding vectors point in nearly the same
direction, so semantic search finds the match.

Behind a small protocol so tests can use a fake and no API key.
"""

from __future__ import annotations

import math
import os
import time
from typing import Protocol

BATCH_SIZE = 50


class EmbeddingUnavailable(RuntimeError):
    """The embedding service can't be used right now. Callers must degrade safely, never crash."""


class Embedder(Protocol):
    model: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def normalize(vector: list[float]) -> list[float]:
    """Scale to length 1, so cosine similarity becomes a plain dot product."""
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector] if norm else list(vector)


def cosine(a: list[float], b: list[float]) -> float:
    """Similarity of two NORMALIZED vectors: 1.0 = same meaning, about 0 = unrelated."""
    return sum(x * y for x, y in zip(a, b))


class GeminiEmbedder:
    """Google Gemini embeddings. Reads GEMINI_API_KEY from the environment."""

    def __init__(self, model: str | None = None, dim: int = 768, client=None) -> None:
        self.model = model or os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")
        self.dim = dim
        try:
            from google import genai

            self.client = client or genai.Client()
        except Exception as e:  # no key configured, package missing
            raise EmbeddingUnavailable("Embeddings are not configured (GEMINI_API_KEY).") from e

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            out += self._embed(texts[i : i + BATCH_SIZE], "RETRIEVAL_DOCUMENT")
            if i + BATCH_SIZE < len(texts):
                time.sleep(1)  # stay under free-tier rate limits when indexing a large KB
        return out

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        from google.genai import errors, types

        try:
            # Documents and queries use different task types: the model is trained so that a
            # QUESTION lands near the passage that ANSWERS it, not near similar questions.
            response = self.client.models.embed_content(
                model=self.model,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=self.dim),
            )
        except errors.APIError as e:
            raise EmbeddingUnavailable(f"Embedding request failed (HTTP {e.code}).") from e
        except Exception as e:  # network errors
            raise EmbeddingUnavailable("Could not reach the embedding service.") from e
        vectors = [normalize(list(e.values)) for e in response.embeddings]
        if len(vectors) != len(texts):
            raise EmbeddingUnavailable("Embedding service returned the wrong number of vectors.")
        return vectors
