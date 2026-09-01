import json
from functools import lru_cache
from pathlib import Path
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# parents[0]=rag/, parents[1]=financial_assistant/, parents[2]=src/, parents[3]=project root
DOCS_PATH = Path(__file__).resolve().parents[3] / "data" / "faq_docs.json"
RELEVANCE_THRESHOLD = 0.12


class FaqRetriever:
    def __init__(self, docs_path: Path = DOCS_PATH):
        self._docs = json.loads(docs_path.read_text())
        corpus = [f"{d['title']} {d['text']}" for d in self._docs]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 1) -> list:
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


class FinancialRetriever:
    """Simple semantic-style retriever for the HisabDo knowledge base."""

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
            stop_words="english"
        )

        self.document_vectors = self.vectorizer.fit_transform(self.texts)

    @staticmethod
    def _document_text(document: Dict) -> str:
        keywords = " ".join(document.get("keywords", []))

        return " ".join([
            document.get("question", ""),
            document.get("answer", ""),
            keywords
        ])

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0
    ) -> List[Dict]:

        if not query.strip():
            return []

        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            self.document_vectors
        )[0]

        ranked_indices = scores.argsort()[::-1]

        results = []

        for index in ranked_indices[:top_k]:
            score = float(scores[index])

            if score < min_score:
                continue

            result = dict(self.documents[index])
            result["score"] = round(score, 4)

            results.append(result)

        return results