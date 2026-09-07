"""
RAG / knowledge-base layer.

Per Day 15 §6.1, this is scoped ONLY to HisabDo product docs, FAQs, and
general financial knowledge — it is never a source for live user data.
TF-IDF cosine similarity is used as a lightweight, dependency-light stand-in
for a real vector search index; the retrieval interface is what the rest
of the code depends on, so swapping in a real vector DB later doesn't
touch callers.
"""
import json
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_PATH = Path(__file__).resolve().parents[2] / "data" / "faq_docs.json"
RELEVANCE_THRESHOLD = 0.12


class FaqRetriever:
    def __init__(self, docs_path: Path = DOCS_PATH):
        self._docs = json.loads(docs_path.read_text())
        corpus = [f"{d['title']} {d['text']}" for d in self._docs]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 1) -> list[dict]:
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
