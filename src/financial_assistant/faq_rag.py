"""
RAG / knowledge-base layer.

Per Day 15 §6.1, this is scoped ONLY to HisabDo product docs, FAQs, and
general financial knowledge — it is never a source for live user data.

Day-7 evaluation rework (docs/dept3-chatbot-evaluation-and-fixes.md). The old
retriever was a single word-level TF-IDF over title + text with a 0.30 threshold.
Root causes it produced in the evaluation:
  * paraphrases with no shared keywords missed ("Explain what this app is for")
  * Roman Urdu / Urdu questions missed (the KB is English)
  * the brand word "HisabDo" alone pulled unrelated questions ("HisabDo support
    phone number?") onto faq-001 - a confident wrong answer
  * no source attribution: callers could not tell which document answered

This version:
  1. indexes each document by title, text AND its `aliases` (other phrasings,
     incl. Roman Urdu / Urdu) from data/faq_docs.json; a document's score is the
     best score of any of its texts
  2. scores with two lexical views: word TF-IDF (1-2 grams) + character n-gram
     TF-IDF (robust to spelling variants and typos, common in Roman Urdu)
  3. expands Roman Urdu / Urdu question words to English and neutralises the
     brand name before scoring
  4. OPTIONAL semantic layer: if an embedding provider is configured
     (EMBEDDING_PROVIDER=openai + OPENAI_API_KEY) the score blends in embedding
     cosine similarity. Off by default: large local models crashed the Render
     deployment before (see xictek_website_assistant/embeddings.py), so this
     stays small unless the team lead approves an embeddings API.
  5. a relevance threshold below which NOTHING is returned (the chatbot then
     says it has no verified answer instead of using an unrelated document)
  6. every result carries id, title and score so the response can cite it
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_PATH = Path(__file__).resolve().parents[2] / "data" / "faq_docs.json"

# Calibrated on tests/evaluation/dept3 (see results/after_fixes.md): every "no verified
# source" question scores below it, every answerable one above it.
RELEVANCE_THRESHOLD = 0.32
WORD_WEIGHT, CHAR_WEIGHT = 0.55, 0.45

_BRAND = re.compile(r"hisab\s?do(\s+ai)?|حساب\s?دو|\b(this|the|your)\s+(app|application)\b|\bapp\b|ایپ", re.I)
# Roman Urdu / Urdu -> English hints, appended to the query (never replacing it).
_EXPANSIONS = {
    "kya": "what", "kia": "what", "kaise": "how", "kese": "how", "kyun": "why", "kyon": "why", "kyu": "why",
    "farq": "difference", "fark": "difference", "munafa": "profit", "aamdani": "revenue income",
    "amdani": "revenue income", "kharcha": "expense spending", "kharche": "expenses", "kharchon": "expenses",
    "kharch": "expense", "udhaar": "credit owed customer balance", "udhar": "credit owed customer balance",
    "zaroori": "important", "matlab": "meaning define", "hisaab": "record", "category": "category categorize",
    "zaban": "language", "zabaan": "language", "samajhta": "understand", "download": "export download",
    "nikalein": "export", "nikalna": "export", "data": "data", "training": "train", "train": "train",
    "paise": "money cash", "aati": "do", "karti": "do",
    "کیا": "what", "کیسے": "how", "کیوں": "why", "فرق": "difference", "منافع": "profit", "آمدنی": "revenue income",
    "خرچ": "expense", "اخراجات": "expenses", "ادھار": "credit owed customer balance", "ایپ": "app",
    "کیش": "cash", "فلو": "flow", "ڈیٹا": "data", "ٹریننگ": "train", "اردو": "urdu", "زبان": "language",
    "کیٹیگری": "category", "ایکسپورٹ": "export", "اسٹیٹمنٹ": "statement",
}
# Everyday English words mapped to the KB's vocabulary (domain synonyms, not question-specific).
_EXPANSIONS.update({
    "left": "remaining remains profit", "remaining": "remains", "costs": "expenses",
    "sales": "revenue income", "earn": "revenue income", "earned": "revenue income", "spending": "expenses",
    "spend": "expenses", "label": "categorize category", "group": "category", "groups": "categories",
    "sorted": "categorized", "spreadsheet": "export csv", "excel": "export csv", "file": "export",
    "learn": "train", "private": "data", "records": "data", "purpose": "what", "owe": "owed credit",
    "owes": "owed credit", "credit": "owed", "language": "languages", "languages": "language",
    "out": "export download",
})
# Roman Urdu / Urdu function words carry no topic; left in, they make every "... kya hota hai?"
# look alike to the character n-gram view.
_FUNCTION_WORDS = {"kya", "kia", "hai", "hain", "hota", "hoti", "hote", "ka", "ki", "ke", "ko", "se", "mein", "main",
                   "aur", "ya", "to", "tou", "bhi", "hi", "na", "nahi", "karna", "karta", "karte", "karti", "kar",
                   "hum", "mujhe", "mera", "meri", "mere", "apne", "apna", "apni", "yeh", "ye", "woh", "wo",
                   "کیا", "ہے", "ہیں", "ہوتا",
                   "ہوتی", "کا", "کی", "کے", "کو",
                   "سے", "میں", "اور", "میرا",
                   "میری"}
_EN_STOP = {"what", "is", "are", "the", "a", "an", "how", "do", "does", "i", "my", "me", "can", "you", "it", "of",
            "to", "for", "in", "on", "per", "this", "that", "your", "with", "and", "or", "be", "app", "tell", "about",
            "explain", "work", "works", "please", "use", "using", "used", "get", "want", "know", "need", "there",
            "does", "one", "sentence", "short", "brief", "briefly", "simple", "words", "purpose", "kind", "type",
            "software", "product", "platform"}
_TOKEN = re.compile(r"\w+", re.UNICODE)


def normalise(text: str) -> str:
    """Lowercase, expand Roman Urdu / Urdu / everyday words to KB vocabulary, drop function words.
    The brand name is removed - unless it is the only topic word ("HisabDo kya hai?")."""
    lowered = text.lower()
    without_brand = _BRAND.sub(" ", lowered)
    tokens = _TOKEN.findall(without_brand)
    topic = [t for t in tokens if t not in _FUNCTION_WORDS and t not in _EN_STOP and not t.isdigit()]
    if not topic and _BRAND.search(lowered):
        tokens = [*tokens, "hisabdo", "bookkeeping", "app"]
    extra = [_EXPANSIONS[t] for t in tokens if t in _EXPANSIONS]
    kept = [t for t in tokens if t not in _FUNCTION_WORDS and t not in _EN_STOP]
    return " ".join([*kept, *extra])


class FaqRetriever:
    def __init__(self, docs_path: Path = DOCS_PATH, threshold: float = RELEVANCE_THRESHOLD, embedder=None):
        self._docs = json.loads(docs_path.read_text(encoding="utf-8"))
        self.threshold = threshold
        self._rows: list[tuple[int, str]] = []
        for i, d in enumerate(self._docs):
            for text in [d["title"], f"{d['title']} {d['text']}", *d.get("aliases", [])]:
                self._rows.append((i, text))
        corpus = [normalise(t) for _, t in self._rows]
        self._word = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self._char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self._word_m = self._word.fit_transform(corpus)
        self._char_m = self._char.fit_transform(corpus)
        self._embedder = embedder
        self._emb_m = embedder.embed([t for _, t in self._rows]) if embedder else None

    def scores(self, query: str) -> list[tuple[int, float, str]]:
        """Best score per document, highest first: (doc index, score, matched text)."""
        q = normalise(query)
        row_scores = (WORD_WEIGHT * cosine_similarity(self._word.transform([q]), self._word_m)[0]
                      + CHAR_WEIGHT * cosine_similarity(self._char.transform([q]), self._char_m)[0])
        if self._embedder is not None:
            qv = self._embedder.embed([query])[0]
            row_scores = 0.5 * row_scores + 0.5 * (self._emb_m @ qv)
        best: dict[int, tuple[float, str]] = {}
        for (doc_i, text), score in zip(self._rows, row_scores):
            if doc_i not in best or score > best[doc_i][0]:
                best[doc_i] = (float(score), text)
        return sorted(((i, s, t) for i, (s, t) in best.items()), key=lambda x: x[1], reverse=True)

    def retrieve(self, query: str, top_k: int = 1) -> list[dict]:
        results = []
        for doc_i, score, matched in self.scores(query)[:top_k]:
            if score >= self.threshold:
                doc = self._docs[doc_i]
                results.append({"id": doc["id"], "title": doc["title"], "text": doc["text"],
                                "score": round(score, 4), "matched": matched})
        return results


class OpenAIEmbedder:
    """Optional semantic layer (text-embedding-3-small). Only used when configured."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        from openai import OpenAI
        self._client, self._model = OpenAI(api_key=api_key, timeout=15, max_retries=1), model

    def embed(self, texts: list[str]) -> np.ndarray:
        data = self._client.embeddings.create(model=self._model, input=texts).data
        m = np.array([d.embedding for d in sorted(data, key=lambda d: d.index)], dtype=np.float32)
        return m / np.linalg.norm(m, axis=1, keepdims=True)


def _configured_embedder():
    if os.getenv("EMBEDDING_PROVIDER", "none").strip().lower() == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            return OpenAIEmbedder(os.environ["OPENAI_API_KEY"])
        except Exception:  # noqa: BLE001 - never block the chatbot; fall back to lexical
            return None
    return None


@lru_cache
def get_retriever() -> FaqRetriever:
    return FaqRetriever(embedder=_configured_embedder())
