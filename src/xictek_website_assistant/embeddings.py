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
import re
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .config import get_xictek_settings

VECTORIZER_FILENAME = "tfidf_vectorizer.pkl"

# Query-side synonym lexicon for common website-visitor intents. A trigger
# word in the visitor's question pulls in related words that the site's FAQ
# entries are likely to use. Extend this dict as real misses show up.
_SYNONYMS: dict[str, str] = {
    "touch": "contact email phone reach",
    "contact": "email phone reach touch",
    "reach": "contact email phone",
    "email": "contact reach",
    "phone": "contact reach call",
    "call": "contact phone reach",
    "based": "located location office address headquarters",
    "located": "based location office address headquarters",
    "location": "based located office address headquarters",
    "address": "location office located based",
    "headquarters": "based located location office",
    "office": "location located address based",
    "price": "pricing cost free paid plan subscription charge",
    "pricing": "price cost free paid plan subscription charge",
    "cost": "price pricing free paid plan charge",
    "free": "price pricing cost paid plan",
    "timeline": "duration long take weeks months typical time",
    "duration": "timeline long take weeks months time",
    "industry": "industries sector clients domain",
    "industries": "industry sector clients domain",
    "sector": "industry industries clients domain",
    "freelance": "contract hire hiring engagement outsourcing dedicated team",
    "contract": "freelance hire engagement outsourcing dedicated team",
    "engagement": "freelance contract hire outsourcing dedicated team",
    "demo": "book schedule consultation meeting call conversation",
    "book": "demo schedule consultation meeting call conversation",
    "blog": "article articles guide post resource",
    "post": "blog article articles guide resource",
    "posts": "blog article articles guide resource",
    "different": "why choose unique difference strengths approach experience",
    "unique": "why choose different strengths approach experience",
    "categorization": "category categories categorize expense",
    "portfolio": "projects project completed work case studies",
    "projects": "portfolio project completed work case studies",
    "platform": "android ios app play store",
    "ios": "iphone apple app store platform android",
    "android": "app play store platform ios",
    "career": "careers job jobs hiring internship vacancy apply roles",
    "careers": "career job jobs hiring internship vacancy apply roles",
    "hiring": "career careers job jobs internship vacancy apply roles",
    "jobs": "career careers hiring internship vacancy apply roles",
    "internships": "internship bootcamp career hiring apply",
    "ai": "artificial intelligence chatbot automation machine learning llm",
    "rag": "retrieval augmented generation ai chatbot knowledge",
    "chatbot": "conversation assistant ai automation",
}
_EXPANSION_WEIGHT = 0.5


def _expand_query(text: str) -> str:
    """Related words for any trigger words in `text` ('' if none)."""
    extra: list[str] = []
    for word in re.findall(r"[a-z]+", text.lower()):
        extra.extend(_SYNONYMS.get(word, "").split())
    return " ".join(dict.fromkeys(extra))


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
    vectorizer = _vectorizer()
    vector = vectorizer.transform([text]).toarray().astype(np.float32)[0]
    expansion = _expand_query(text)
    if expansion:
        extra = vectorizer.transform([expansion]).toarray().astype(np.float32)[0]
        vector = vector + _EXPANSION_WEIGHT * extra
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector = vector / norm
    return vector
