import json
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_PATH = Path(__file__).resolve().parents[2] / "data" / "faq_docs.json"
RELEVANCE_THRESHOLD = 0.30


class FaqRetriever:
    def __init__(self, docs_path: Path = DOCS_PATH):
        self.docs_path = docs_path
        self._load_index()

    def _load_index(self):
        docs = json.loads(self.docs_path.read_text(encoding="utf-8"))
        if not isinstance(docs, list) or not docs:
            raise ValueError("Knowledge base must contain a non-empty document list")

        for doc in docs:
            if not isinstance(doc, dict) or not doc.get("title") or not doc.get("text"):
                raise ValueError("Knowledge base contains an invalid document")

        corpus = [f"{doc['title']} {doc['text']}" for doc in docs]
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus)

        self._docs = docs
        self._vectorizer = vectorizer
        self._matrix = matrix

    def refresh(self) -> bool:
        try:
            candidate = FaqRetriever(self.docs_path)
            self._docs = candidate._docs
            self._vectorizer = candidate._vectorizer
            self._matrix = candidate._matrix
            return True
        except Exception:
            return False

    def retrieve(self, query: str, top_k: int = 1) -> list[dict]:
        if not query or not query.strip() or top_k <= 0:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked_idx = scores.argsort()[::-1][:top_k]

        return [
            {**self._docs[idx], "score": float(scores[idx])}
            for idx in ranked_idx
            if scores[idx] >= RELEVANCE_THRESHOLD
        ]


@lru_cache
def get_retriever() -> FaqRetriever:
    return FaqRetriever()
