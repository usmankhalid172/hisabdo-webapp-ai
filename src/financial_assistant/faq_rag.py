
import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_PATH = Path(__file__).resolve().parents[2] / "data" / "faq_docs.json"
RELEVANCE_THRESHOLD = 0.30
EMBEDDING_MODEL = "text-embedding-3-small"


class FaqRetriever:
    """FAQ retrieval using OpenAI semantic embeddings with offline fallback."""

    def __init__(self, docs_path: Path = DOCS_PATH):
        self._docs = json.loads(docs_path.read_text(encoding="utf-8"))
        if not self._docs:
            raise ValueError("Knowledge base cannot be empty.")

        self._texts = [
            f"{doc.get('title', '')} {doc.get('text', '')}"
            for doc in self._docs
        ]
        self._client = None
        self._embeddings = None

        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI

                self._client = OpenAI()
                response = self._client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=self._texts,
                )
                self._embeddings = self._normalize(
                    [item.embedding for item in response.data]
                )
            except Exception:
                self._client = None
                self._embeddings = None

        if self._embeddings is None:
            self._vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
            )
            self._matrix = self._vectorizer.fit_transform(self._texts)

    @staticmethod
    def _normalize(vectors):
        vectors = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)

    def retrieve(self, query: str, top_k: int = 1) -> list[dict]:
        if not query or not query.strip() or top_k < 1:
            return []

        if self._client is not None and self._embeddings is not None:
            try:
                response = self._client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=[query.strip()],
                )
                query_vector = self._normalize(
                    [response.data[0].embedding]
                )[0]
                scores = self._embeddings @ query_vector
            except Exception:
                return []
        else:
            query_vector = self._vectorizer.transform([query.strip()])
            scores = cosine_similarity(query_vector, self._matrix)[0]

        ranked = np.argsort(scores)[::-1]
        results = []

        for index in ranked:
            score = float(scores[index])
            if score < RELEVANCE_THRESHOLD:
                break

            results.append({
                **self._docs[index],
                "score": round(score, 4),
                "source": self._docs[index].get("id", "unknown"),
            })
            if len(results) >= top_k:
                break

        return results


@lru_cache
def get_retriever() -> FaqRetriever:
    return FaqRetriever()