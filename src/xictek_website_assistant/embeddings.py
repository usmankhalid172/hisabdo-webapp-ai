"""
Local TF-IDF lexical embeddings (replaces the sentence-transformers
multilingual model). Mirrors src/financial_assistant/rag/retriever.py's
approach: sklearn TfidfVectorizer, no torch, no model download, no
network at query time, sub-second fit even at this corpus size.

TRADE-OFF (flagged to the team lead, not a silent downgrade): TF-IDF is
literal keyword overlap, not semantic similarity, so retrieval quality
for paraphrased queries is weaker than the multilingual model gave us.
It also cannot match a non-English query against this English-language
site content by itself -- translate the query to English before
calling embed_query() when the message isn't in English (see
service.py). This swap exists specifically to fix the 502s/timeouts on
Render caused by the ~470MB model's cold-start download+load, given no
ability to change Render's plan or build config from this codebase.

Persistence: TfidfVectorizer must be FIT on the corpus (it needs every
chunk's text to compute IDF weights), and the exact same fitted
vectorizer must be reused to transform new queries later -- unlike a
pretrained model, it can't be reconstructed from nothing. embed_texts()
(called once, by ingest.py, with the full chunk corpus) fits and
persists the vectorizer. embed_query() (called per request) loads that
persisted vectorizer lazily and only ever calls .transform(), never
re-fits, so query vectors stay in the same space the corpus vectors
were built in.
"""
from __future__ import annotations

import pickle
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .config import get_xictek_settings

VECTORIZER_FILENAME = "tfidf_vectorizer.pkl"


def embed_texts(texts: list[str]) -> np.ndarray:
    """Fits a fresh TfidfVectorizer on `texts` and returns an
    (n_texts, vocab_size) float32 L2-normalized dense array. Called once
    by ingest.py with the full corpus -- persists the fitted vectorizer
    to disk so embed_query() can reuse the exact same vector space."""
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", norm="l2", ngram_range=(1, 2), max_df=0.5, min_df=2)
    matrix = vectorizer.fit_transform(texts)
    index_dir = get_xictek_settings().index_dir
    index_dir.mkdir(parents=True, exist_ok=True)
    with open(index_dir / VECTORIZER_FILENAME, "wb") as f:
        pickle.dump(vectorizer, f)
    return matrix.toarray().astype(np.float32)


@lru_cache
def _vectorizer() -> TfidfVectorizer:
    index_dir = get_xictek_settings().index_dir
    with open(index_dir / VECTORIZER_FILENAME, "rb") as f:
        return pickle.load(f)


def embed_query(text: str) -> np.ndarray:
    """Transforms a single query into the SAME vector space the corpus
    was embedded in -- loads the vectorizer persisted by embed_texts()
    during ingest, never re-fits. Translate non-English queries to
    English before calling this: TF-IDF only matches literal tokens, so
    it cannot bridge languages the way the old multilingual model could."""
    vector = _vectorizer().transform([text])
    return vector.toarray().astype(np.float32)[0]
