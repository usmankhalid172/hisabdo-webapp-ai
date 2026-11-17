"""Department 3 retrieval strategy benchmark (docs/dept3-retrieval-strategy-matrix.md).

Benchmarks dense-only against hybrid BM25 + vector retrieval, and measures what query rewriting, the router gate,
metadata filtering (product section / feature category) and cross-encoder reranking each add. Every strategy is
scored twice: with the production parameters (threshold 0.566273, top 2, margin 0.05; or each retriever's own scale)
and with parameters calibrated on the 139 judged evaluation queries (dev + held-out).

The test target is the Day 1 failed set: the 19 judged queries that fail in production (comparison.json, C10) plus
20 probe questions from the Phase 2 Day 1 review (queries_failed_day1_probe.json, never used for calibration).

    python scripts/retrieval_strategy_benchmark.py   -> data/retrieval_eval/results/strategy_benchmark.json
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval_eval as R  # noqa: E402
from build_dept3_knowledge_set import MODULE_BY_AREA  # noqa: E402
from src.financial_assistant.grounding.retrieval import HYBRID_ALPHA, bm25_unit, normalise, rewrite  # noqa: E402

DATA = ROOT / "data" / "retrieval_eval"
OUT = DATA / "results" / "strategy_benchmark.json"
PRODUCTION = {"threshold": 0.566273, "top_k": 2, "margin": 0.05}

# Metadata filter: the product section a question is about, and whether it asks about the app (feature) or about
# bookkeeping practice (concept). Applied to the rewritten query, so Urdu and Roman Urdu are covered by the glossary.
MODULE_CUES = {
    "expenses_income": r"expense|spend|income|categor|petrol|rent|budget|recurring",
    "customers_udhar": r"udhar|customer|owe|credit|dues|receivable",
    "suppliers_payables": r"supplier|payable|vendor",
    "khata_ledger": r"khata|ledger",
    "reports_pdf": r"report|pdf|statement|export|excel|analytics|share",
    "data_backup_sync": r"backup|sync|cloud|uninstall|restore|lose|change.*phone|new phone|offline|internet",
    "privacy_security": r"privacy|secure|safe|accountant|see my|third part",
    "app_platform": r"android|ios|iphone|web|desktop|version|download|install|bank",
    "language_currency": r"currenc|language|urdu|english",
}
MODULE_RE = {m: re.compile(p) for m, p in MODULE_CUES.items()}
FEATURE_Q = re.compile(r"hisabdo|\bapp\b|\bcan i\b|\bhow do i\b|\bdoes it\b|\bmy (khata|expenses|records|data)\b|"
                       r"\bsync|\bexport|\bpdf\b|\bbackup|\binstall")
CONCEPT_Q = re.compile(r"\bwhat is\b|\bdifference\b|\bshould\b|\bhow much .* keep\b|\bis .* a business expense\b")
W_MODULE, W_FEATURE = 0.06, 0.04


@dataclass
class Strategy:
    name: str
    retriever: str              # dense_bge | hybrid | bm25
    rewrite: bool = False
    gate: bool = False          # team intent router: only faq-routed questions reach the KB
    metadata: bool = False      # product-section boost + feature-category boost + legal scope filter
    rerank: bool = False        # bge cross-encoder over the top 20
    production: bool = False


STRATEGIES = [
    Strategy("S1 Dense (bge-small) only", "dense_bge"),
    Strategy("S2 Dense + query rewrite", "dense_bge", rewrite=True),
    Strategy("S3 Hybrid BM25 + dense", "hybrid"),
    Strategy("S4 Hybrid + query rewrite", "hybrid", rewrite=True),
    Strategy("S5 S4 + router gate (production)", "hybrid", rewrite=True, gate=True, production=True),
    Strategy("S6 S5 + metadata filter", "hybrid", rewrite=True, gate=True, metadata=True),
    Strategy("S7 S5 + rerank", "hybrid", rewrite=True, gate=True, rerank=True),
    Strategy("S8 S5 + metadata filter + rerank", "hybrid", rewrite=True, gate=True, metadata=True, rerank=True),
    Strategy("S9 BM25 + rewrite + gate (lexical fallback)", "bm25", rewrite=True, gate=True),
    Strategy("S10 Dense + rewrite + router gate", "dense_bge", rewrite=True, gate=True),
]


def query_modules(q: str) -> set[str]:
    return {m for m, rx in MODULE_RE.items() if rx.search(q)}


class Bench:
    def __init__(self):
        self.p = R.Pipeline(R.load_chunks())
        self.chunks = self.p.chunks
        self.module = np.array([MODULE_BY_AREA.get(c["area"].replace(" (general practice)", ""), "general_bookkeeping")
                                for c in self.chunks])
        self.product = np.array([c["category"] in ("product_faq", "product_guide") for c in self.chunks])
        self.legal = np.array([c["category"] == "legal_policy" for c in self.chunks])
        self._ce: dict = {}

    def rank(self, s: Strategy, text: str) -> tuple[list[tuple[int, float]], dict]:
        info: dict = {}
        if s.gate:
            intent = self.p.router.recognize(text, R.ROUTER_DAY).intent.value
            info["intent"] = intent
            if intent != "faq":
                return [], {**info, "gated": intent}
        q = rewrite(text) if s.rewrite else normalise(text)
        info["query_used"] = q
        if s.retriever == "hybrid":
            sc = HYBRID_ALPHA * self.p.r["dense_bge"].scores(q) + (1 - HYBRID_ALPHA) * bm25_unit(
                self.p.r["bm25"].scores(q))
        else:
            sc = self.p.r[s.retriever].scores(q)
        boost = np.zeros(len(self.chunks))
        if s.metadata:
            mods = query_modules(q.lower())
            info["modules"] = sorted(mods)
            if mods:
                boost += W_MODULE * np.isin(self.module, list(mods))
            if FEATURE_Q.search(q.lower()) and not CONCEPT_Q.search(q.lower()):
                info["feature_question"] = True
                boost += W_FEATURE * self.product
            if not R.LEGAL_TERMS.search(q.lower()):
                sc = np.where(self.legal, -np.inf, sc)
            sc = sc + boost
        order = [int(i) for i in np.argsort(-sc)[:20] if np.isfinite(sc[i])]
        if s.rerank:
            key = (q, tuple(order))
            if key not in self._ce:
                self._ce[key] = self.p.reranker.scores(q, [self.p.texts[i] for i in order]).tolist()
            pairs = [(i, ce + 10 * boost[i]) for i, ce in zip(order, self._ce[key])]
            return sorted(pairs, key=lambda x: -x[1]), info
        return [(i, float(sc[i])) for i in order], info


def per_type(rows: list[dict], types: dict[str, str]) -> dict:
    out = defaultdict(lambda: [0, 0])
    for r in rows:
        t = types.get(r["id"])
        if t:
            out[t][0] += r["ok"]
            out[t][1] += 1
    return {k: f"{a}/{b}" for k, (a, b) in sorted(out.items())}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    qrels = R.load_qrels()
    calib = R.load_queries("queries_dev_day1.json") + R.load_queries("queries_heldout.json")
    comp = json.loads((DATA / "results" / "comparison.json").read_text(encoding="utf-8"))
    prod_rows = next(c for c in comp["configs"] if c["name"].startswith("C10"))["production"]["rows"]
    failed_ids = [r["id"] for r in prod_rows if not r["ok"]]
    by_id = {q["id"]: q for q in calib}
    probe = json.loads((DATA / "queries_failed_day1_probe.json").read_text(encoding="utf-8"))["queries"]
    for q in probe:
        qrels[q["id"]] = q["qrels"]
    failed = [by_id[i] for i in failed_ids] + probe
    types = {q["id"]: q["type"] for q in probe}
    for i in failed_ids:  # type of an evaluation query from its id (H-EXP-EN-1 -> EXP)
        tag = re.sub(r"^H-(H\d?-)?", "", i).split("-")[0]
        types[i] = {"EXP": "feature_how_to", "INC": "feature_how_to", "UDH": "udhar_khata", "KHA": "udhar_khata",
                    "PDF": "reports_export", "GEN": "platform_currency", "TC": "not_knowledge"}.get(
            tag, "udhar_khata" if i in ("D16",) else "data_sync_privacy")

    b = Bench()
    known = {c["id"] for c in b.chunks}
    missing = [(q["id"], c) for q in probe for c in q["qrels"] if c not in known]
    assert not missing, missing

    only = sys.argv[1] if len(sys.argv) > 1 else None   # e.g. S10: run one strategy, merge into the saved file
    results = []
    for s in [x for x in STRATEGIES if not only or x.name.split()[0] == only]:
        t0 = time.perf_counter()
        ranked = {}
        traces = {}
        for q in calib + probe:
            ranked[q["id"]], traces[q["id"]] = b.rank(s, q["text"])
        ms = (time.perf_counter() - t0) * 1000 / (len(calib) + len(probe))
        best, _ = R.sweep(calib, ranked, b.chunks, qrels)
        params = {"production": PRODUCTION if s.retriever == "hybrid" and not s.rerank else None,
                  "calibrated": {k: best[k] for k in ("threshold", "top_k", "margin")}}
        entry = {"strategy": asdict(s), "latency_ms": round(ms, 1), "safe_range": best["safe_range"]}
        for label, prm in params.items():
            if prm is None:
                continue
            ev_c = R.judge(calib, ranked, b.chunks, qrels, prm["threshold"], prm["top_k"], prm["margin"])
            ev_f = R.judge(failed, ranked, b.chunks, qrels, prm["threshold"], prm["top_k"], prm["margin"])
            ev_p = R.judge(probe, ranked, b.chunks, qrels, prm["threshold"], prm["top_k"], prm["margin"])
            entry[label] = {
                "params": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in prm.items()},
                "calibration_139": R.summary(ev_c),
                "failed_set_39": {**R.summary(ev_f), "by_type": per_type(ev_f["rows"], types),
                                  "fixed_of_19_production_failures": sum(r["ok"] for r in ev_f["rows"][:19])},
                "probe_20_unseen": R.summary(ev_p),
                "failed_rows": [{**r, "type": types[r["id"]], "trace": traces[r["id"]]} for r in ev_f["rows"]],
            }
        results.append(entry)
        c = entry["calibrated"]
        print(f"{s.name:44} cal {c['calibration_139']['correct']}/139  failed {c['failed_set_39']['correct']}/39  "
              f"probe {c['probe_20_unseen']['correct']}/20  unrel {c['failed_set_39']['unrelated_in_context']}  "
              f"{c['params']}  {ms:.0f} ms", flush=True)
    if only and OUT.exists():
        old = json.loads(OUT.read_text(encoding="utf-8"))["results"]
        results = [r for r in old if r["strategy"]["name"].split()[0] != only] + results
        results.sort(key=lambda r: int(r["strategy"]["name"].split()[0][1:]))
    OUT.write_text(json.dumps({"failed_ids": failed_ids, "types": types, "results": results}, indent=1,
                              ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
