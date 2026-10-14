"""Test doubles for semantic search: no API key, no network.

ConceptEmbedder is a tiny hand-made "meaning" model: each dimension is one concept,
and English and Roman Urdu words for the same idea share a dimension. That lets the
tests prove the thing embeddings are for: matching text that shares NO words.
"""

import re
from pathlib import Path

from chatbot.embeddings import EmbeddingUnavailable, normalize

FIXTURES = Path(__file__).parent / "fixtures"

CONCEPTS = [
    {"expense", "expenses", "kharcha", "kharche", "spend", "spent"},
    {"record", "add", "likhun", "likhna", "enter", "save"},
    {"price", "pricing", "cost", "plan", "qeemat"},
    {"export", "excel", "pdf", "download"},
    {"credit", "udhaar", "limit", "had", "owe", "baqi"},
    {"payment", "payments", "received", "wapis"},
    {"report", "reports", "summary"},
    {"biryani", "recipe", "cook", "cricket", "weather"},
]


class ConceptEmbedder:
    model = "concept-test-model"

    def __init__(self) -> None:
        self.document_calls: list[list[str]] = []
        self.fail = False

    def _vector(self, text: str) -> list[float]:
        words = re.findall(r"[a-z]+", text.lower())
        return normalize([float(sum(w in concept for w in words)) for concept in CONCEPTS])

    def embed_documents(self, texts):
        if self.fail:
            raise EmbeddingUnavailable("simulated outage")
        self.document_calls.append(list(texts))
        return [self._vector(t) for t in texts]

    def embed_query(self, text):
        if self.fail:
            raise EmbeddingUnavailable("simulated outage")
        return self._vector(text)


def shared_words(a: str, b: str) -> set[str]:
    """What keyword matching would see: words (3+ letters) present in both texts."""
    tokens = lambda t: {w for w in re.findall(r"[a-z]+", t.lower()) if len(w) >= 3}  # noqa: E731
    return tokens(a) & tokens(b)
