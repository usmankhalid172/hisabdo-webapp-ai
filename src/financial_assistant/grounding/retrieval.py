"""Retrieval over the approved knowledge base (data/kb/approved/kb_chunks.jsonl).

Shared by the chatbot and by the evaluation harness (scripts/retrieval_eval.py), so the code that is measured is the
code that runs. Configuration measured on 2026-10-28 (docs/retrieval-approach-comparison.md, C10): router gate ->
normalise + rewrite -> hybrid 0.6 x bge-small-en cosine + 0.4 x BM25/(BM25+5) -> threshold 0.586, top-k 2, margin 0.05.

The dense half needs `fastembed` (local ONNX model, no API key). Without it the retriever runs lexical only (BM25 on
the rewritten query) with its own measured threshold; see LEXICAL_* below.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
KB_PATH = ROOT / "data" / "kb" / "approved" / "kb_chunks.jsonl"

BGE = "BAAI/bge-small-en-v1.5"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
MAX_QUERY_CHARS = 512  # Day 1 #19: a 100,000-character message must not reach the retriever whole

# ------------------------------------------------------------------------------------ normalisation

STOP = set("""a an the is are am be been was were do does did of to in on for with at by from and or but if then
so as it its this that these those i me my we our you your he she they them what which who whom how can could
should would will shall may might there here about into than too very just not no yes any some""".split())
ROMAN_STOP = set("ka ki ke ko hai hain ho hun mein main se aur bhi to ye yeh woh wo kya".split())

# Roman Urdu / Urdu -> English terms used in the KB. Written from the Day 1 questions and general finance
# vocabulary BEFORE the held-out questions were read; frozen afterwards (see docs).
GLOSSARY = {
    # app and product
    "hisabdo": "hisabdo", "ہساب": "hisabdo", "حسابدو": "hisabdo",
    "app": "app", "ایپ": "app", "aplikeshan": "app",
    "muft": "free", "مفت": "free", "free": "free", "paisa lagta": "price cost free",
    "qeemat": "price cost", "قیمت": "price cost", "fees": "price cost free", "fee": "price cost free",
    "internet": "internet offline", "انٹرنیٹ": "internet offline", "offline": "offline internet",
    "net": "internet offline",
    "backup": "backup restore", "بیک": "backup", "بیکاپ": "backup restore",
    "restore": "restore backup", "wapas": "restore",
    "phone": "phone device", "فون": "phone device", "mobile": "phone device", "موبائل": "phone device",
    "badal": "change new phone", "badalna": "change new phone", "badlun": "change new phone", "نیا": "new",
    "naya": "new", "nayi": "new",
    "data": "data records", "ڈیٹا": "data records",
    "mehfooz": "safe secure", "محفوظ": "safe secure", "safe": "safe secure backup",
    "report": "report pdf", "رپورٹ": "report pdf", "pdf": "pdf report statement", "statement": "statement pdf",
    "bhejna": "send share", "bhejo": "send share", "bhej": "send share", "بھیج": "send share",
    "zuban": "language", "zaban": "language", "زبان": "language", "urdu": "urdu language", "اردو": "urdu language",
    "currency": "currency", "کرنسی": "currency", "rupay": "currency pkr", "rupee": "currency pkr",
    "iphone": "iphone ios", "android": "android",
    "awaz": "voice", "آواز": "voice", "bol": "voice",
    "rabta": "contact support", "رابطہ": "contact support", "madad": "help support", "مدد": "help support",
    "delete": "delete data", "mitana": "delete", "hatana": "delete", "ختم": "delete",
    "account": "account sign in", "login": "sign in account",
    # ledger and finance concepts
    "khata": "khata ledger", "کھاتہ": "khata ledger", "کھاتا": "khata ledger", "کھاتے": "khata ledger",
    "hisab": "ledger account", "hisaab": "ledger account", "حساب": "ledger account",
    "udhar": "udhar credit dues receivable", "udhaar": "udhar credit dues receivable",
    "ادھار": "udhar credit dues receivable",
    "qarz": "debt payable owe", "قرض": "debt payable owe", "baqaya": "outstanding balance dues", "بقایا": "outstanding balance dues",
    "kharcha": "expense", "kharch": "expense", "kharche": "expenses", "خرچہ": "expense", "خرچ": "expense",
    "aamdani": "income", "amdani": "income", "آمدنی": "income", "kamai": "income earnings", "کمائی": "income earnings",
    "munafa": "profit", "منافع": "profit", "nuksan": "loss", "نقصان": "loss",
    "farq": "difference", "فرق": "difference", "matlab": "meaning definition", "مطلب": "meaning definition",
    "grahak": "customer", "customer": "customer", "گاہک": "customer", "supplier": "supplier", "سپلائر": "supplier",
    "payment": "payment", "ادائیگی": "payment", "adaigi": "payment", "raqam": "amount", "رقم": "amount",
    "len": "receivable", "dain": "payable", "lena": "receivable", "dena": "payable",
    # question words
    "kaise": "how", "کیسے": "how", "kyun": "why", "کیوں": "why", "kab": "when", "کب": "when",
    "kahan": "where", "کہاں": "where", "kon": "who", "kaun": "who", "کون": "who",
    "kitna": "how much", "kitni": "how much", "kitne": "how much", "کتنا": "how much", "کتنی": "how much",
    "kya": "", "کیا": "",
}
URDU_RANGE = r"؀-ۿ"
TOKEN = re.compile(rf"[a-z0-9]+|[{URDU_RANGE}]+")


def normalise(text: str) -> str:
    """Unicode NFKC, lower case, punctuation to spaces, collapsed whitespace, length cap."""
    text = unicodedata.normalize("NFKC", text)[:MAX_QUERY_CHARS].lower()
    text = re.sub(rf"[^a-z0-9{URDU_RANGE}\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def rewrite(text: str) -> str:
    """Normalised query plus English equivalents of Roman Urdu / Urdu terms (the original words are kept)."""
    norm = normalise(text)
    extra = []
    for phrase, english in GLOSSARY.items():
        if " " in phrase:
            if phrase in norm:
                extra.append(english)
        elif re.search(rf"(?<![a-z0-9{URDU_RANGE}]){re.escape(phrase)}(?![a-z0-9{URDU_RANGE}])", norm):
            extra.append(english)
    extra = " ".join(e for e in extra if e)
    return f"{norm} {extra}".strip() if extra else norm


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP and t not in ROMAN_STOP and len(t) > 1]


# ------------------------------------------------------------------------------------ corpus


def passage(c: dict) -> str:
    """Text indexed for a chunk: page title, heading and body, so a chunk carries its own context."""
    return f"{c['title']}. {c['heading']}.\n{c['body']}"


class BM25:
    name = "bm25"

    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75):
        self.docs = [Counter(tokens(t)) for t in texts]
        self.len = np.array([sum(d.values()) for d in self.docs], dtype=float)
        self.avg = self.len.mean()
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def scores(self, q: str) -> np.ndarray:
        out = np.zeros(len(self.docs))
        for t in set(tokens(q)):
            idf = self.idf.get(t)
            if idf is None:
                continue
            tf = np.array([d.get(t, 0) for d in self.docs], dtype=float)
            out += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.len / self.avg))
        return out


def bm25_unit(s: np.ndarray, k: float = 5.0) -> np.ndarray:
    """BM25 squashed to 0..1 without per-query normalisation, so a threshold keeps one meaning across queries."""
    return s / (s + k)


# ------------------------------------------------------------------------------------ retriever used by the chatbot

# Measured parameters (data/retrieval_eval/results/comparison.json, production params; tests check they match).
HYBRID_ALPHA = 0.6
HYBRID_THRESHOLD, HYBRID_TOP_K, HYBRID_MARGIN = 0.585804, 2, 0.05   # C10
LEXICAL_THRESHOLD, LEXICAL_TOP_K, LEXICAL_MARGIN = 4.940, 2, 2.0     # C15, used when fastembed is not installed
CANDIDATES = 20


@dataclass(frozen=True)
class Passage:
    """One approved KB chunk as the answer layer sees it."""
    chunk_id: str
    title: str
    section: str
    heading: str
    body: str
    source_id: str
    source_url: str
    category: str
    usage: str           # "answer" | "reference_only" (legal pages: quote and link, do not interpret)
    last_updated: str | None
    status: str          # "active" | "needs_confirmation" (sources disagree; see notes)
    notes: tuple[str, ...]
    score: float = 0.0

    @property
    def label(self) -> str:
        """How the source is named in a reply: page title and section."""
        section = self.heading if self.category == "product_faq" else self.section
        return f"{self.title} › {section}"


def load_kb(path: Path = KB_PATH) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class KbRetriever:
    """Hybrid (dense + BM25) when fastembed is available, else BM25 on the rewritten query. Returns only passages that
    pass the measured threshold, top-k and margin, so an empty list means: no supporting source."""

    def __init__(self, chunks: list[dict] | None = None, mode: str = "auto"):
        self.chunks = chunks if chunks is not None else load_kb()
        self.texts = [passage(c) for c in self.chunks]
        self.bm25 = BM25(self.texts)
        self.dense = None
        if mode in ("auto", "hybrid"):
            try:
                from fastembed import TextEmbedding
                self.dense = TextEmbedding(BGE)
                docs = np.array(list(self.dense.embed(self.texts)))
                self.doc_vectors = docs / np.linalg.norm(docs, axis=1, keepdims=True)
            except ImportError:
                if mode == "hybrid":
                    raise
        self.mode = "hybrid" if self.dense is not None else "lexical"

    def scores(self, query: str) -> np.ndarray:
        q = rewrite(query)
        lexical = self.bm25.scores(q)
        if self.dense is None:
            return lexical
        v = np.array(list(self.dense.embed([BGE_QUERY_PREFIX + q])))[0]
        return HYBRID_ALPHA * (self.doc_vectors @ (v / np.linalg.norm(v))) + (1 - HYBRID_ALPHA) * bm25_unit(lexical)

    def retrieve(self, query: str) -> list[Passage]:
        threshold, top_k, margin = ((HYBRID_THRESHOLD, HYBRID_TOP_K, HYBRID_MARGIN) if self.mode == "hybrid"
                                    else (LEXICAL_THRESHOLD, LEXICAL_TOP_K, LEXICAL_MARGIN))
        s = self.scores(query)
        order = [int(i) for i in np.argsort(-s)[:CANDIDATES]]
        if not order or s[order[0]] < threshold:
            return []
        best = s[order[0]]
        keep = [i for i in order if s[i] >= threshold and s[i] >= best - margin][:top_k]
        return [to_passage(self.chunks[i], float(s[i])) for i in keep]


def to_passage(c: dict, score: float = 0.0) -> Passage:
    return Passage(chunk_id=c["id"], title=c["title"], section=c["section"], heading=c["heading"], body=c["body"],
                   source_id=c["source_id"], source_url=c["source_url"], category=c["category"],
                   usage=c.get("usage", "answer"), last_updated=c.get("last_updated"),
                   status=c.get("status", "active"), notes=tuple(c.get("notes") or ()), score=score)
