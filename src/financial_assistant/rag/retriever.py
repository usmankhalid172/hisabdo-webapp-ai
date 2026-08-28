from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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