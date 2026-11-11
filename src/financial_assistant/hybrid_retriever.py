import json
import re
import unicodedata
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_DOCS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "faq_docs.json"
)


def normalize_query(query: str) -> str:
    """Normalize Unicode, casing, whitespace and surrounding punctuation."""
    if not isinstance(query, str):
        return ""
    query = unicodedata.normalize("NFKC", query)
    query = query.lower()
    query = re.sub(r"\s+", " ", query).strip()
    return query.strip(" .,!?;:")


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


class HybridFaqRetriever:
    """Combine BM25 lexical retrieval and TF-IDF semantic matching."""

    def __init__(self, docs_path: Path = DEFAULT_DOCS_PATH):
        self.docs = json.loads(
            Path(docs_path).read_text(encoding="utf-8-sig")
        )

        if not self.docs:
            raise ValueError("Knowledge base cannot be empty.")

        self.texts = [
            f"{doc.get('title', '')} {doc.get('text', '')}"
            for doc in self.docs
        ]

        tokenized_corpus = [tokenize(text) for text in self.texts]

        self.bm25 = BM25Okapi(tokenized_corpus)

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        bm25_weight: float = 0.5,
        tfidf_weight: float = 0.5,
        product_area: str | None = None,
        category: str | None = None,
        section: str | None = None,
    ) -> list[dict]:

        if not query or not query.strip() or top_k < 1:
            return []

        if bm25_weight < 0 or tfidf_weight < 0:
            raise ValueError("Retrieval weights cannot be negative.")

        if bm25_weight + tfidf_weight == 0:
            raise ValueError("At least one retrieval weight must be positive.")

        normalized_query = normalize_query(query)
        tokens = tokenize(normalized_query)
        if not tokens:
            return []
        ambiguous_balance_phrases = {
            "balance",
            "the balance",
            "show balance",
            "show me the balance",
            "please show me the balance",
            "tell me the balance",
            "what is the balance",
            "what's the balance",
            "can you show me the balance",
        }
        if normalized_query in ambiguous_balance_phrases:
            return []

        # Never retrieve unrelated FAQs for an unsupported integration.
        corpus_text = " ".join(self.texts).lower()
        if "quickbooks" in tokens and "quickbooks" not in corpus_text:
            return []

        # Reject unsupported queries with no meaningful topic-word overlap.
        vocabulary = set(self.vectorizer.get_feature_names_out())
        generic_tokens = {
            "hisabdo", "integrate", "integrates", "integrated",
            "integration", "support", "supports", "supported",
        }
        content_tokens = [
            token for token in tokens
            if token not in ENGLISH_STOP_WORDS
            and token not in generic_tokens
        ]
        if content_tokens and not any(
            token in vocabulary for token in content_tokens
        ):
            return []

        # Apply metadata filters before ranking retrieval results.
        filters = {
            "product_area": product_area,
            "category": category,
            "section": section,
        }

        allowed_indices = [
            i for i, doc in enumerate(self.docs)
            if all(
                value is None
                or str(doc.get(field, "")).casefold() == value.strip().casefold()
                for field, value in filters.items()
            )
        ]

        if not allowed_indices:
            return []

        bm25_scores = np.asarray(self.bm25.get_scores(tokens), dtype=float)

        query_vector = self.vectorizer.transform([normalized_query])
        tfidf_scores = cosine_similarity(
            query_vector, self.matrix
        )[0]

        bm25_ranked = [
            int(i) for i in np.argsort(bm25_scores)[::-1]
            if bm25_scores[i] > 0
        ]

        tfidf_ranked = [
            int(i) for i in np.argsort(tfidf_scores)[::-1]
            if tfidf_scores[i] > 0
        ]

        hybrid_scores = {}

        for rank, index in enumerate(bm25_ranked, start=1):
            hybrid_scores[index] = (
                hybrid_scores.get(index, 0.0)
                + bm25_weight / (60 + rank)
            )

        for rank, index in enumerate(tfidf_ranked, start=1):
            hybrid_scores[index] = (
                hybrid_scores.get(index, 0.0)
                + tfidf_weight / (60 + rank)
            )

        ranked = sorted(
            (i for i in hybrid_scores if i in allowed_indices),
            key=lambda i: (-hybrid_scores[i], i),
        )

        results = []

        for index in ranked[:top_k]:
            result = dict(self.docs[index])
            result["score"] = round(hybrid_scores[index], 6)
            result["hybrid_score"] = round(hybrid_scores[index], 6)
            result["bm25_score"] = round(float(bm25_scores[index]), 4)
            result["tfidf_score"] = round(float(tfidf_scores[index]), 4)
            result["source"] = result.get("id", "unknown")
            results.append(result)

        return results
