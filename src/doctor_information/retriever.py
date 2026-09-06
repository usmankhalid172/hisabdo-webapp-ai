from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class DoctorRetriever:
    """TF-IDF retriever for doctor profile and schedule information."""

    def __init__(
        self,
        documents: List[Dict],
        relevance_threshold: float = 0.12,
    ):
        if not documents:
            raise ValueError("Doctor documents cannot be empty.")

        self.documents = documents
        self.relevance_threshold = relevance_threshold

        self.texts = [
            self._document_text(document)
            for document in documents
        ]

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
        )

        self.document_vectors = self.vectorizer.fit_transform(
            self.texts
        )

    @staticmethod
    def _document_text(document: Dict) -> str:
        schedule = document.get("schedule", {})

        schedule_text = " ".join(
            f"{day} {hours}"
            for day, hours in schedule.items()
        )

        return " ".join([
            document.get("name", ""),
            document.get("specialty", ""),
            document.get("qualifications", ""),
            schedule_text,
        ])

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[Dict]:
        """Return relevant doctor records for a user query."""

        if not isinstance(query, str) or not query.strip():
            return []

        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            self.document_vectors,
        )[0]

        ranked_indices = scores.argsort()[::-1]

        results = []

        for index in ranked_indices[:top_k]:
            score = float(scores[index])

            if score < self.relevance_threshold:
                continue

            result = dict(self.documents[index])
            result["score"] = round(score, 4)
            results.append(result)

        return results