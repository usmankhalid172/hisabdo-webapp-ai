"""
FAQ / product-docs retriever used by the chatbot service layer.

Per Day 15 A6.1 this retriever is scoped ONLY to HisabDo product docs, FAQs,
and general financial knowledge - it is never a source for live user data.
TF-IDF cosine similarity is a lightweight, dependency-light stand-in for a
real vector search index; the retrieval interface is what callers depend on,
so swapping in a real vector store later does not touch callers.

This module lives under the ``rag`` *package* (not ``rag.py``) to avoid the
module-vs-package name collision that previously broke the chatbot import
(Task 26 endpoint-connection fix).

Error handling (Task 26): fetching the document context (the JSON corpus)
must never crash the backend. ``FaqRetriever.retrieve`` short-circuits to an
empty result list when the corpus is missing, unreadable, or malformed, so
the service layer can gracefully fall back to a general reply instead of a
500.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# data/faq_docs.json lives at <repo-root>/src/financial_assistant/rag/faq.py
# -> parents[2] is src/, parents[3] is repo root.
DOCS_PATH = Path(__file__).resolve().parents[3] / "data" / "faq_docs.json"
RELEVANCE_THRESHOLD = 0.12


class FaqRetriever:
    """TF-IDF retriever over the HisabDo FAQ/product-docs corpus."""

    def __init__(self, docs_path: Path = DOCS_PATH):
        self.docs_path = Path(docs_path)
        # Load lazily so a missing/corrupt corpus surfaces as "no matches"
        # during retrieval rather than at construction time.
        self._docs: List[Dict] = []
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = None
        self._load()

    def _load(self) -> None:
        try:
            self._docs = json.loads(self.docs_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            # Document context unavailable - degrade to an empty corpus so
            # callers can fall back gracefully instead of crashing.
            self._docs = []
            return
        if not isinstance(self._docs, list):
            self._docs = []
            return
        corpus = [f"{d['title']} {d['text']}" for d in self._docs]
        # An all-empty corpus would make TfidfVectorizer fit fail.
        if not corpus or not any("".join(corpus).strip()):
            self._docs = []
            return
        self._matrix = self._vectorizer.fit_transform(corpus)

    @property
    def loaded(self) -> bool:
        """True when the document corpus was loaded and indexed successfully."""
        return bool(self._docs) and self._matrix is not None

    def retrieve(self, query: str, top_k: int = 1) -> list[dict]:
        if not self.loaded or self._matrix is None:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked_idx = scores.argsort()[::-1][:top_k]

        results = []
        for idx in ranked_idx:
            if scores[idx] >= RELEVANCE_THRESHOLD:
                results.append({**self._docs[idx], "score": float(scores[idx])})
        return results


@lru_cache
def get_retriever() -> FaqRetriever:
    return FaqRetriever()
