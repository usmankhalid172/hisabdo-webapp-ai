"""Measured comparison of retrieval approaches for the HisabDo knowledge base.

Corpus: data/kb/approved/kb_chunks.jsonl (364 cleaned chunks from the 23 approved sources).
Tuning set: data/retrieval_eval/queries_dev_day1.json (the Day 1 failed questions).
Held-out set: data/retrieval_eval/queries_heldout.json (team question sets + off-topic), used once.
Judgments: data/retrieval_eval/qrels.json, graded 2 = answers the question, 1 = related background,
0 / missing = unrelated. Pools for judging come from every method's top results.

    python scripts/retrieval_eval.py heldout   # build the held-out query file from the team sets
    python scripts/retrieval_eval.py pool      # list unjudged (query, passage) pairs to judge
    python scripts/retrieval_eval.py run       # tune on Day 1, evaluate on held-out, write results

Needs `fastembed` (local ONNX models, CPU, no API key) for the dense and reranking methods.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.financial_assistant.grounding.retrieval import (  # noqa: E402  shared with the chatbot
    BGE, BGE_QUERY_PREFIX, BM25, GLOSSARY, MAX_QUERY_CHARS, ROMAN_STOP, STOP, TOKEN, URDU_RANGE, bm25_unit,
    normalise, passage, rewrite, tokens)

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "data" / "retrieval_eval"
KB = ROOT / "data" / "kb" / "approved" / "kb_chunks.jsonl"
CACHE = Path.home() / ".cache" / "hisabdo_retrieval_eval"

MINILM_ML = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RERANKER = "Xenova/ms-marco-MiniLM-L-6-v2"

# ------------------------------------------------------------------------------------ normalisation

# ------------------------------------------------------------------------------------ metadata gate

MINE = r"(?:\bmy\b|\bmera\b|\bmeri\b|\bmere\b|میرا|میری|میرے|\bi\b|\bmujhe\b|\bhum\b|\bhamari\b|\bour\b)"
FIGURES = (r"(?:total|balance|sales?|earn\w*|spent|spend\w*|profit|income|owe[sd]?|paise|baqaya|kamai|"
           r"kharch\w*|munafa|bikri|بیلنس|سیل|کمائی|پیسے|خرچ\w*)")
ASKING = r"(?:how much|what (?:is|are)|show|tell me|kitn\w*|kitn|batao|bata\w*|dikha\w*|بتاؤ|بتائیں|کتن\w*|دکھا\w*)"
THIRD_PARTY = (r"(?:\b[a-z]+ (?:ka|ki|ke) (?:hisaa?b|khata|account|balance|kharch\w*|udhaa?r)\b|"
               r"\b[a-z]+'s (?:balance|account|ledger|khata|transactions)\b|"
               r"\b(?:bhai|biwi|behen|behan|dost|walid|abbu|ammi|wife|husband|brother|sister|friend|user \d+)\b|"
               r"[{u}]+ (?:کا|کی|کے) (?:کھاتہ|کھاتا|حساب|بیلنس|اکاؤنٹ)|بھائی|بیوی|بہن|دوست)").format(u=URDU_RANGE)
ACTION = (r"(?:\b(?:kholo|khol do|khol|dikhao|dikha do|open)\b.*\b(?:hisaa?b|khata|account|ledger)\b|"
          r"\b(?:hisaa?b|khata|account|ledger)\b.*\b(?:kholo|khol do|dikhao|dikha do)\b|کھولیں|کھولو)")
TRANSACTION = (r"(?:\b\d[\d,]*\b.*\b(?:diye|liye|mile|milay|bheje|nahi|tha|thi|paid|received|spent|gave|got)\b|"
               r"\b(?:galti|ghalti|correction|ghalat)\b|\b(?:diye|liye)\b.*\b\d[\d,]*\b)")


def personal_or_action(text: str) -> str | None:
    """Why a message is not a knowledge question, or None. The router decides the route; this gate only keeps
    KB passages out of the context for own-figure, third-party, open-ledger and transaction messages."""
    q = normalise(text)
    if re.search(THIRD_PARTY, q):
        return "third_party_or_private"
    if re.search(ACTION, q):
        return "open_ledger_action"
    if re.search(TRANSACTION, q):
        return "transaction_or_correction"
    if re.search(MINE, q) and re.search(FIGURES, q) and re.search(ASKING, q):
        return "own_figures"
    return None


# ------------------------------------------------------------------------------------ corpus and retrievers


def load_chunks() -> list[dict]:
    return [json.loads(line) for line in KB.read_text(encoding="utf-8").splitlines()]


class TfIdf:
    """The production algorithm (src/financial_assistant/faq_rag.py): sklearn TF-IDF, English stop words."""
    name = "tfidf"

    def __init__(self, texts: list[str]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.v = TfidfVectorizer(stop_words="english")
        self.m = self.v.fit_transform(texts)

    def scores(self, q: str) -> np.ndarray:
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity(self.v.transform([q]), self.m)[0]


class Dense:
    def __init__(self, model: str, texts: list[str]):
        from fastembed import TextEmbedding
        self.name = "dense_bge" if model == BGE else "dense_mml"
        self.model_name = model
        self.m = TextEmbedding(model)
        key = hashlib.sha256((model + "\n".join(texts)).encode()).hexdigest()[:16]
        cache = CACHE / f"{key}.npy"
        if cache.exists():
            self.docs = np.load(cache)
        else:
            self.docs = self._unit(np.array(list(self.m.embed(texts))))
            CACHE.mkdir(parents=True, exist_ok=True)
            np.save(cache, self.docs)

    @staticmethod
    def _unit(x: np.ndarray) -> np.ndarray:
        return x / np.linalg.norm(x, axis=1, keepdims=True)

    def scores(self, q: str) -> np.ndarray:
        if self.model_name == BGE:
            q = BGE_QUERY_PREFIX + q
        v = self._unit(np.array(list(self.m.embed([q]))))[0]
        return self.docs @ v


class Reranker:
    def __init__(self):
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        self.m = TextCrossEncoder(RERANKER)

    def scores(self, q: str, texts: list[str]) -> np.ndarray:
        return np.array(list(self.m.rerank(q, texts)))


# ------------------------------------------------------------------------------------ pipelines


@dataclass
class Config:
    name: str
    retriever: str            # tfidf | bm25 | dense_bge | dense_mml | hybrid
    rewrite: bool = False     # Roman Urdu / Urdu glossary expansion
    rerank: bool = False      # cross-encoder over the hybrid candidates
    gate: str | None = None   # None | "rules" (regex gate) | "router" (team intent router; see ROUTER_TO_KB)
    kb_intents: tuple = ("faq",)  # router intents allowed to reach the KB
    scope_filter: bool = False  # legal chunks only for privacy/legal questions; needs_confirmation kept
    alpha: float = 0.6        # hybrid weight on the dense score
    candidates: int = 20
    note: str = ""


LEGAL_TERMS = re.compile(r"privacy|policy|terms|legal|third.part|share my|sell|delete|rights|retention|children|"
                         r"cookies|advert|liabilit|disclaimer|personal information|collect|law|security|secure|safe")


class Pipeline:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        texts = [passage(c) for c in chunks]
        self.texts = texts
        self.r = {"tfidf": TfIdf(texts), "bm25": BM25(texts), "dense_bge": Dense(BGE, texts),
                  "dense_mml": Dense(MINILM_ML, texts)}
        self.reranker = Reranker()
        self.legal = np.array([c["category"] == "legal_policy" for c in chunks])
        self._ce_cache: dict = {}
        sys.path.insert(0, str(ROOT))
        from src.financial_assistant.dialogue.recognizer import RuleBasedIntentRecognizer
        self.router = RuleBasedIntentRecognizer()

    def rank(self, cfg: Config, query: str) -> tuple[list[tuple[int, float]], dict]:
        """Ranked (chunk index, score) before threshold/top-k, plus trace info."""
        info = {"query_used": query}
        if cfg.gate == "rules" and (why := personal_or_action(query)):
            return [], {**info, "gated": why}
        if cfg.gate == "router":
            intent = self.router.recognize(query, ROUTER_DAY).intent.value
            info["intent"] = intent
            if intent not in cfg.kb_intents:
                return [], {**info, "gated": f"router intent {intent}"}
        q = rewrite(query) if cfg.rewrite else (normalise(query) if cfg.retriever != "tfidf" else query[:MAX_QUERY_CHARS])
        info["query_used"] = q
        if cfg.retriever == "hybrid":
            dense = self.r["dense_bge"].scores(q)
            lex = bm25_unit(self.r["bm25"].scores(q))
            s = cfg.alpha * dense + (1 - cfg.alpha) * lex
        else:
            s = self.r[cfg.retriever].scores(q)
        if cfg.scope_filter and not LEGAL_TERMS.search(q):
            s = np.where(self.legal, -np.inf, s)
        order = [int(i) for i in np.argsort(-s)[: cfg.candidates] if np.isfinite(s[i])]
        if cfg.rerank:
            key = (q, tuple(order))
            if key not in self._ce_cache:  # configs that differ only in gating share reranker scores
                self._ce_cache[key] = self.reranker.scores(q, [self.texts[i] for i in order]).tolist()
            pairs = sorted(zip(order, self._ce_cache[key]), key=lambda p: -p[1])
            return pairs, info
        return [(i, float(s[i])) for i in order], info


CONFIGS = [
    Config("C1 TF-IDF (production algorithm)", "tfidf", note="faq_rag.py algorithm on the new KB"),
    Config("C2 BM25", "bm25", rewrite=False),
    Config("C3 Dense bge-small-en", "dense_bge"),
    Config("C4 Dense multilingual MiniLM", "dense_mml"),
    Config("C5 Hybrid BM25+bge", "hybrid"),
    Config("C6 Hybrid + query rewrite", "hybrid", rewrite=True),
    Config("C7 Hybrid + rewrite + rerank", "hybrid", rewrite=True, rerank=True),
    Config("C8 C7 + rule gate", "hybrid", rewrite=True, rerank=True, gate="rules"),
    Config("C9 C8 + scope filter", "hybrid", rewrite=True, rerank=True, gate="rules", scope_filter=True),
    Config("C10 C6 + router gate (faq)", "hybrid", rewrite=True, gate="router"),
    Config("C11 C7 + router gate (faq)", "hybrid", rewrite=True, rerank=True, gate="router"),
    Config("C12 C6 + router gate (faq+general)", "hybrid", rewrite=True, gate="router", kb_intents=("faq", "general")),
    Config("C13 C7 + router gate (faq+general)", "hybrid", rewrite=True, rerank=True, gate="router",
           kb_intents=("faq", "general")),
    Config("C14 C13 + scope filter", "hybrid", rewrite=True, rerank=True, gate="router", kb_intents=("faq", "general"),
           scope_filter=True),
    Config("C15 BM25 + rewrite + router gate (faq)", "bm25", rewrite=True, gate="router",
           note="lexical fallback for servers without fastembed"),
]
ROUTER_DAY = __import__("datetime").date(2026, 10, 28)


# ------------------------------------------------------------------------------------ evaluation


def load_queries(name: str) -> list[dict]:
    return json.loads((EVAL / name).read_text(encoding="utf-8"))["queries"]


def load_qrels() -> dict[str, dict[str, int]]:
    p = EVAL / "qrels.json"
    return json.loads(p.read_text(encoding="utf-8"))["judgments"] if p.exists() else {}


def expectation(q: dict, qrels: dict) -> str:
    """'answer' only when the judges found a fully relevant passage; otherwise the KB cannot answer it."""
    if q["expect"] in ("answer", "optional") and not any(g == 2 for g in qrels.get(q["id"], {}).values()):
        return "no_answer_in_kb"
    return "no_answer_in_kb" if q["expect"] == "optional" else q["expect"]


def select(ranked: list[tuple[int, float]], threshold: float, top_k: int, margin: float | None) -> list[tuple[int, float]]:
    """Passages that reach the context: score >= threshold, within `margin` of the best, at most top_k."""
    if not ranked:
        return []
    best = ranked[0][1]
    keep = [(i, s) for i, s in ranked if s >= threshold and (margin is None or s >= best - margin)]
    return keep[:top_k]


def judge(queries, ranked_all, chunks, qrels, threshold, top_k, margin) -> dict:
    rows, ok = [], 0
    hit_k = rr_sum = n_ans = 0
    unrelated = included = relevant_included = 0
    for q in queries:
        exp = expectation(q, qrels)
        ranked = ranked_all[q["id"]]
        ctx = select(ranked, threshold, top_k, margin)
        grades = [qrels.get(q["id"], {}).get(chunks[i]["id"], 0) for i, _ in ctx]
        if exp == "answer":
            n_ans += 1
            full = [r for r, (i, _) in enumerate(ranked) if qrels.get(q["id"], {}).get(chunks[i]["id"], 0) == 2]
            hit_k += 2 in grades  # recall = an answering passage actually reached the context
            rr_sum += 1 / (full[0] + 1) if full else 0
            good = 2 in grades and 0 not in grades
        elif exp == "none":
            good = not ctx
        else:
            good = 0 not in grades
        unrelated += grades.count(0)
        included += len(grades)
        relevant_included += sum(1 for g in grades if g >= 1)
        ok += good
        rows.append({"id": q["id"], "expect": exp, "ok": bool(good), "context": [
            {"chunk": chunks[i]["id"], "score": round(s, 4), "grade": g} for (i, s), g in zip(ctx, grades)]})
    n = len(queries)
    return {"correct": ok, "n": n, "accuracy": ok / n if n else 0,
            "answerable": n_ans, "recall_at_k": hit_k / n_ans if n_ans else 0, "mrr": rr_sum / n_ans if n_ans else 0,
            "unrelated_in_context": unrelated, "passages_in_context": included,
            "context_precision": relevant_included / included if included else 1.0, "rows": rows}


TOP_KS = (1, 2, 3, 4, 5, 8)
MAX_CUTS = 150
MARGINS = (None, 0.05, 0.1, 0.2, 0.3, 1.0, 2.0, 3.0)


def sweep(queries, ranked_all, chunks, qrels) -> tuple[dict, list[dict]]:
    """Choose threshold, top-k and margin from measured results, not estimates.

    Threshold candidates are the midpoints between scores observed on these queries. Objective: most queries
    fully correct; then fewest unrelated passages in the context. Among the thresholds that tie, take the middle
    of the longest unbroken run of tied cuts, so the cut sits in the centre of the safe range rather than at an
    edge (the first version took the edge and over-fitted; see docs).
    """
    scores = sorted({round(s, 6) for q in queries for _, s in ranked_all[q["id"]][:max(TOP_KS)]})
    cuts = [(a + b) / 2 for a, b in zip(scores, scores[1:])] or [0.0]
    if len(cuts) > MAX_CUTS:  # evenly spaced through the observed scores keeps the sweep fast
        cuts = [cuts[round(i * (len(cuts) - 1) / (MAX_CUTS - 1))] for i in range(MAX_CUTS)]
    grid, best = [], None
    for top_k in TOP_KS:
        for margin in MARGINS:
            results = [judge(queries, ranked_all, chunks, qrels, t, top_k, margin) for t in cuts]
            keyed = [(r["correct"], -r["unrelated_in_context"]) for r in results]
            top = max(keyed)
            runs, start = [], None  # unbroken runs of cut indices that reach the best score
            for i, k in enumerate(keyed + [None]):
                if k == top and start is None:
                    start = i
                elif k != top and start is not None:
                    runs.append((start, i - 1))
                    start = None
            lo, hi = max(runs, key=lambda r: (r[1] - r[0], r[0]))
            mid = (lo + hi) // 2
            r = results[mid]
            g = {"threshold": cuts[mid], "top_k": top_k, "margin": margin, "correct": r["correct"],
                 "unrelated": r["unrelated_in_context"], "recall": r["recall_at_k"],
                 "precision": r["context_precision"], "passages": r["passages_in_context"],
                 "safe_range": [cuts[lo], cuts[hi]], "safe_run_length": hi - lo + 1}
            grid.append(g)
            if best is None or (g["correct"], -g["unrelated"], g["safe_run_length"], g["recall"]) > \
                    (best["correct"], -best["unrelated"], best["safe_run_length"], best["recall"]):
                best = g
    return best, grid


def score_all(pipe: Pipeline, cfg: Config, queries: list[dict]) -> tuple[dict, dict, float]:
    ranked, traces = {}, {}
    t0 = time.perf_counter()
    for q in queries:
        ranked[q["id"]], traces[q["id"]] = pipe.rank(cfg, q["text"])
    ms = (time.perf_counter() - t0) * 1000 / max(1, len(queries))
    return ranked, traces, ms


# ------------------------------------------------------------------------------------ commands


def cmd_heldout() -> None:
    dev = {normalise(q["text"]) for q in load_queries("queries_dev_day1.json")}
    out, seen = [], set(dev)
    for f in ["multilingual_product_test_cases.json", "multilingual_product_test_cases_heldout.json",
              "multilingual_product_test_cases_heldout_v2.json", "multilingual_product_test_cases_heldout_v3.json"]:
        d = json.loads((ROOT / "data" / f).read_text(encoding="utf-8"))
        items = d["cases"] if "cases" in d else next(v for v in d.values() if isinstance(v, list))
        for i in items:
            key = normalise(i["text"])
            if key in seen:
                continue
            seen.add(key)
            out.append({"id": f"H-{i['id']}", "lang": i["language"], "text": i["text"],
                        "expect": "answer" if i["expect_intent"] == "faq" else "none",
                        "from": f"{f} ({i['expect_intent']})"})
    acc = json.loads((ROOT / "data" / "release_acceptance_cases.json").read_text(encoding="utf-8"))["cases"]
    labels = {"TC-02": "none", "TC-03": "none", "TC-06": "none", "TC-07": "optional", "TC-08": "none",
              "F-01": "answer", "F-05": "answer", "P-06": "none", "P-08": "none"}
    for c in acc:
        if c["id"] in labels and normalise(c["message"]) not in seen:
            seen.add(normalise(c["message"]))
            out.append({"id": f"H-{c['id']}", "lang": "en", "text": c["message"], "expect": labels[c["id"]],
                        "from": "release_acceptance_cases.json"})
    offtopic = ["What's the weather in Lahore today?", "Who won yesterday's cricket match?",
                "Write a short poem about the sea.", "What is the capital of France?", "Give me a biryani recipe.",
                "Tell me a joke.", "How do I install Python on Windows?", "Translate good morning into French.",
                "Aaj Karachi mein mausam kaisa hai?", "کرکٹ میچ کس نے جیتا؟"]
    for n, t in enumerate(offtopic, 1):
        out.append({"id": f"H-OT-{n:02d}", "lang": "ur" if re.search(f"[{URDU_RANGE}]", t) else
                    ("roman_ur" if "mein" in t else "en"), "text": t, "expect": "none", "from": "off-topic (written for this test)"})
    doc = {"description": "Held-out set. Never used for tuning. Product questions (expect_intent faq) must be "
                          "answered from the KB; every other team label (own figures, transactions, other people's "
                          "accounts) and the off-topic questions must get an empty context.",
           "queries": out}
    (EVAL / "queries_heldout.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(out)} held-out queries: {Counter(q['expect'] for q in out)}")


def cmd_pool(depth: int) -> None:
    chunks = load_chunks()
    pipe = Pipeline(chunks)
    qrels = load_qrels()
    queries = [q for f in ("queries_dev_day1.json", "queries_heldout.json") for q in load_queries(f)
               if q["expect"] in ("answer", "optional", "no_answer_in_kb")]
    lines = []
    for q in queries:
        pool = []
        for cfg in CONFIGS:
            ranked, _ = pipe.rank(Config(cfg.name, cfg.retriever, cfg.rewrite, cfg.rerank), q["text"])
            pool += [chunks[i]["id"] for i, _ in ranked[:depth]]
        todo = [c for c in dict.fromkeys(pool) if c not in qrels.get(q["id"], {})]
        if todo:
            lines.append(f"### {q['id']} [{q['lang']}] {q['text']}")
            by_id = {c["id"]: c for c in chunks}
            for cid in todo:
                c = by_id[cid]
                lines.append(f"  {cid} | {c['heading'][:70]} | {c['body'][:260].replace(chr(10), ' ')}")
    out = EVAL / "pool_to_judge.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{sum(1 for l in lines if l.startswith('  '))} unjudged pairs for "
          f"{sum(1 for l in lines if l.startswith('###'))} queries -> {out}")


def folds(held: list[dict]) -> tuple[list[dict], list[dict]]:
    """Two halves of the held-out set, stratified by expected outcome, assigned by a hash of the id."""
    a, b = [], []
    for exp in sorted({q["expect"] for q in held}):
        group = sorted((q for q in held if q["expect"] == exp),
                       key=lambda q: hashlib.sha256(q["id"].encode()).hexdigest())
        a += group[0::2]
        b += group[1::2]
    return a, b


def summary(r: dict) -> dict:
    return {k: v for k, v in r.items() if k != "rows"}


def cmd_run(only: str | None = None) -> None:
    chunks = load_chunks()
    pipe = Pipeline(chunks)
    qrels = load_qrels()
    dev, held = load_queries("queries_dev_day1.json"), load_queries("queries_heldout.json")
    fold_a, fold_b = folds(held)
    results = {"kb_chunks": len(chunks), "dev_queries": len(dev), "heldout_queries": len(held),
               "folds": {"A": [q["id"] for q in fold_a], "B": [q["id"] for q in fold_b]}, "configs": []}
    previous = []
    if only:  # re-measure one configuration and keep the stored results of the others
        previous = [c for c in json.loads((EVAL / "results" / "comparison.json").read_text(encoding="utf-8"))["configs"]
                    if not c["name"].startswith(only + " ")]
    for cfg in [c for c in CONFIGS if not only or c.name.startswith(only + " ")]:
        ranked, traces, ms = score_all(pipe, cfg, dev + held)
        # 1. Tuned on the Day 1 questions only (the brief): kept to show how far 19 questions generalise.
        p1, _ = sweep(dev, ranked, chunks, qrels)
        day1_only = judge(held, ranked, chunks, qrels, p1["threshold"], p1["top_k"], p1["margin"])
        # 2. Two-fold cross-validation: tune on Day 1 + one half, test on the other half, then swap.
        cv_rows, cv_params = [], {}
        for name, tune, test in (("A", fold_a, fold_b), ("B", fold_b, fold_a)):
            p, _ = sweep(dev + tune, ranked, chunks, qrels)
            cv_params[f"tuned_on_day1+{name}"] = p
            cv_rows += judge(test, ranked, chunks, qrels, p["threshold"], p["top_k"], p["margin"])["rows"]
        cv = judge_rows_summary(cv_rows, held, qrels)
        # 3. Production parameters: tuned on everything; the cross-validated numbers are the estimate for them.
        prod, grid = sweep(dev + held, ranked, chunks, qrels)
        dev_r = judge(dev, ranked, chunks, qrels, prod["threshold"], prod["top_k"], prod["margin"])
        all_r = judge(dev + held, ranked, chunks, qrels, prod["threshold"], prod["top_k"], prod["margin"])
        for r in all_r["rows"]:
            r["trace"] = traces[r["id"]]
        results["configs"].append({
            "name": cfg.name, "config": cfg.__dict__, "latency_ms_per_query": round(ms, 1),
            "day1_only": {"params": p1, "heldout": summary(day1_only)},
            "cross_validated": {"params": cv_params, "heldout": cv},
            "production": {"params": prod, "day1": summary(dev_r), "all": summary(all_r), "rows": all_r["rows"]},
            "grid": grid})
        print(f"{cfg.name:34} day1-only held {day1_only['correct']:3}/{len(held)} unrel {day1_only['unrelated_in_context']:3} | "
              f"CV held {cv['correct']:3}/{len(held)} recall {cv['recall_at_k']:.2f} prec {cv['context_precision']:.2f} "
              f"unrel {cv['unrelated_in_context']:3} | prod t={prod['threshold']:+.3f} k={prod['top_k']} m={prod['margin']} "
              f"day1 {dev_r['correct']}/{len(dev)} | {ms:.0f} ms")
    if only:
        order = {c.name: i for i, c in enumerate(CONFIGS)}
        results["configs"] = sorted(previous + results["configs"], key=lambda c: order.get(c["name"], 99))
    (EVAL / "results").mkdir(exist_ok=True)
    (EVAL / "results" / "comparison.json").write_text(
        json.dumps(rounded(results), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def rounded(x):
    """Floats to 6 decimals: smaller files, and long digit runs are not mistaken for phone numbers by the scanner."""
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, dict):
        return {k: rounded(v) for k, v in x.items()}
    if isinstance(x, list):
        return [rounded(v) for v in x]
    return x


def judge_rows_summary(rows: list[dict], queries: list[dict], qrels: dict) -> dict:
    """Aggregate per-query rows produced under different (fold) parameters."""
    n_ans = sum(1 for r in rows if r["expect"] == "answer")
    grades = [c["grade"] for r in rows for c in r["context"]]
    hits = sum(1 for r in rows if r["expect"] == "answer" and any(c["grade"] == 2 for c in r["context"]))
    by_expect = {}
    for r in rows:
        e = by_expect.setdefault(r["expect"], [0, 0])
        e[0] += r["ok"]
        e[1] += 1
    return {"correct": sum(r["ok"] for r in rows), "n": len(rows), "accuracy": sum(r["ok"] for r in rows) / len(rows),
            "answerable": n_ans, "recall_at_k": hits / n_ans if n_ans else 0,
            "unrelated_in_context": grades.count(0), "passages_in_context": len(grades),
            "context_precision": sum(1 for g in grades if g >= 1) / len(grades) if grades else 1.0,
            "by_expect": {k: f"{v[0]}/{v[1]}" for k, v in by_expect.items()}, "rows": rows}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["heldout", "pool", "run"])
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--only", help="config prefix, e.g. C15: re-measure only that configuration")
    a = ap.parse_args()
    {"heldout": cmd_heldout, "pool": lambda: cmd_pool(a.depth), "run": lambda: cmd_run(a.only)}[a.command]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
