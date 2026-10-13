import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_PATH = Path(__file__).resolve().parents[3] / "data" / "faq_docs.json"
RELEVANCE_THRESHOLD = 0.30


class FaqRetriever:
    """Retrieve relevant HisabDo FAQs using TF-IDF vector similarity."""

    def __init__(self, docs_path: Path = DOCS_PATH):
        self._docs = json.loads(docs_path.read_text(encoding="utf-8"))
        if not self._docs:
            raise ValueError("Knowledge base cannot be empty.")

        corpus = [
            f"{doc.get('title', '')} {doc.get('text', '')}"
            for doc in self._docs
        ]
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self._matrix = self._vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 1) -> list[dict]:
        if not query or not query.strip() or top_k < 1:
            return []

        query_vec = self._vectorizer.transform([query.strip()])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked_idx = scores.argsort()[::-1]

        results = []
        for idx in ranked_idx:
            score = float(scores[idx])
            if score < RELEVANCE_THRESHOLD:
                break

            results.append({
                **self._docs[idx],
                "score": round(score, 4),
                "source": self._docs[idx].get("id", "unknown"),
            })
            if len(results) >= top_k:
                break

        return results


@lru_cache
def get_retriever() -> FaqRetriever:
    return FaqRetriever()


class FinancialRetriever:
    """Lightweight TF-IDF retriever for general financial knowledge."""

    def __init__(self, documents: List[Dict]):
        if not documents:
            raise ValueError("Documents cannot be empty.")

        self.documents = documents
        self.texts = [
            self._document_text(document)
            for document in documents
        ]
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
        )
        self.document_vectors = self.vectorizer.fit_transform(self.texts)

    @staticmethod
    def _document_text(document: Dict) -> str:
        keywords = " ".join(document.get("keywords", []))
        return " ".join([
            document.get("question", ""),
            document.get("answer", ""),
            keywords,
        ])

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> List[Dict]:
        if not query or not query.strip() or top_k < 1:
            return []

        query_vector = self.vectorizer.transform([query.strip()])
        scores = cosine_similarity(
            query_vector,
            self.document_vectors,
        )[0]
        ranked_indices = scores.argsort()[::-1]

        results = []
        for index in ranked_indices:
            score = float(scores[index])
            if score < min_score:
                break
            result = dict(self.documents[index])
            result["score"] = round(score, 4)
            results.append(result)
            if len(results) >= top_k:
                break

        return results