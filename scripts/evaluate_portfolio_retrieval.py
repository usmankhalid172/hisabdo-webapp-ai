"""Dependency-free retrieval comparison for the XICTEK portfolio fact corpus.

Run from ``hisabdo-webapp-ai`` with ``python scripts/evaluate_portfolio_retrieval.py``.
The checked-in vector index currently has no chunk metadata, so this benchmark
uses the source FAQ facts and reports passage-level retrieval, not app vectors.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAQ = ROOT / "src/xictek_website_assistant/data/xictek_faq_raw.jsonl"

QUERIES = [
    ("What is HisabDo?", ("offline-first digital ledger",)),
    ("Which technologies power HisabDo?", ("Flutter, Supabase, and PostgreSQL",)),
    ("What challenge does the HisabDo project address?", ("paper registers",)),
    ("How does HisabDo solve that problem?", ("offline-first workflows",)),
    ("What are the outcomes or measurable results?", ("public portfolio source does not provide quantified",)),
    ("Show me the product screens or portfolio visuals.", ("Product screenshots of the dashboard",)),
    ("What is XICTEK's flagship product?", ("HisabDo is the flagship product",)),
    ("Does the portfolio include other published case studies?", ("publishes work only when it can be shared responsibly",)),
    ("What services can I discuss after viewing their work?", ("custom software projects with the same product focus",)),
    ("How can I start a custom project conversation?", ("Start a conversation",)),
    ("What does HisabDo do for customer balances and khata?", ("khata (credit and debit records)",)),
    ("What platform and database are used for the ledger?", ("Flutter, Supabase, and PostgreSQL",)),
]

NORMALIZE = {
    "tech": "technology technologies stack", "stack": "technology technologies",
    "screenshots": "screens visuals dashboard", "visuals": "screens screenshots",
    "case": "project portfolio work", "studies": "projects portfolio work",
    "results": "outcomes impact metrics quantified", "measurable": "metrics quantified outcomes",
    "solve": "solution addresses designed", "powers": "built technologies uses",
    "platform": "technology technologies built", "database": "postgresql database",
    "khata": "credit debit ledger records", "visual": "screenshots dashboard workflows",
    "screens": "screenshots dashboard workflows",
}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower().replace("offline-first", "offline first"))


def load_docs() -> list[dict[str, str]]:
    docs = []
    for line in FAQ.read_text(encoding="utf-8").splitlines():
        page = json.loads(line)
        for i, fact in enumerate(page.get("facts", [])):
            docs.append({"id": f"{page['url']}#{i}", "url": page["url"],
                         "text": f"{fact['question']} {fact['answer']}"})
    return docs


def cosine(a: list[str], b: list[str]) -> float:
    ca, cb = {}, {}
    for t in a: ca[t] = ca.get(t, 0) + 1
    for t in b: cb[t] = cb.get(t, 0) + 1
    dot = sum(n * cb.get(t, 0) for t, n in ca.items())
    na = math.sqrt(sum(n*n for n in ca.values()))
    nb = math.sqrt(sum(n*n for n in cb.values()))
    return dot / (na * nb) if na and nb else 0.0


def rank(docs, query, mode):
    qt = tokens(query)
    expanded = qt + [v for t in qt for v in NORMALIZE.get(t, "").split()]
    scored = []
    for d in docs:
        dt = tokens(d["text"])
        base = cosine(qt, dt)
        if mode == "baseline": score = base
        elif mode == "normalized": score = cosine(expanded, dt)
        else:
            # Hybrid: normalized cosine plus a bounded exact-token coverage signal.
            coverage = len(set(expanded) & set(dt)) / max(len(set(expanded)), 1)
            score = 0.65 * cosine(expanded, dt) + 0.35 * coverage
            if mode == "reranked":
                # Lightweight second-stage exact phrase/answer-token rerank.
                answer = d["text"].lower()
                phrase = 1.0 if any(p.lower() in answer for p in ("Flutter, Supabase, and PostgreSQL", "offline-first digital ledger")) else 0.0
                score = 0.80 * score + 0.20 * (len(set(qt) & set(dt)) / max(len(set(qt)), 1) + phrase) / (1 + phrase)
        scored.append((score, d))
    return sorted(scored, key=lambda x: (-x[0], x[1]["id"]))


def metrics(docs, k):
    rows = {"baseline": [], "normalized": [], "hybrid": [], "reranked": []}
    for query, expected_bits in QUERIES:
        relevant = {d["id"] for d in docs if any(bit.lower() in d["text"].lower() for bit in expected_bits)}
        for mode in rows:
            ranked = rank(docs, query, mode)
            hits = [i for i, (_, d) in enumerate(ranked[:k], 1) if d["id"] in relevant]
            rows[mode].append((hits, ranked))
    for mode, cases in rows.items():
        p = sum(bool(h) for h, _ in cases) / len(cases)
        recall = sum(min(len(h), 1) for h, _ in cases) / len(cases)
        mrr = sum((1 / h[0]) if h else 0 for h, _ in cases) / len(cases)
        rel_ids = [{d["id"] for d in docs if any(bit.lower() in d["text"].lower() for bit in bits)} for _, bits in QUERIES]
        precision = sum(sum(1 for _, d in ranked[:k] if d["id"] in rel_ids[i]) / k for i, (_, ranked) in enumerate(cases)) / len(cases)
        print(f"{mode:10} hit@{k}={p:.3f} precision@{k}={precision:.3f} MRR={mrr:.3f}")
    print("\nPortfolio-source-only hybrid tuning (threshold is hybrid score):")
    portfolio_docs = [d for d in docs if d["url"].rstrip("/").endswith("/portfolio")]
    for top_k in (1, 2, 3, 4):
        for threshold in (0.15, 0.20, 0.25, 0.30):
            hit = precision_sum = mrr_sum = 0.0
            for query, expected_bits in QUERIES:
                relevant = {d["id"] for d in portfolio_docs if any(bit.lower() in d["text"].lower() for bit in expected_bits)}
                ranked = [(s, d) for s, d in rank(portfolio_docs, query, "hybrid") if s >= threshold][:top_k]
                hits = [i for i, (_, d) in enumerate(ranked, 1) if d["id"] in relevant]
                hit += bool(hits)
                precision_sum += sum(1 for _, d in ranked if d["id"] in relevant) / top_k
                mrr_sum += 1 / hits[0] if hits else 0
            n = len(QUERIES)
            print(f"top_k={top_k} threshold={threshold:.2f} hit={hit/n:.3f} precision={precision_sum/n:.3f} MRR={mrr_sum/n:.3f}")
    print("\nPer-query reranked top passages:")
    for query, expected in QUERIES:
        results = rank(docs, query, "reranked")[:k]
        print(f"- {query}")
        for score, d in results:
            mark = "*" if any(bit.lower() in d["text"].lower() for bit in expected) else " "
            print(f"  {mark} {score:.3f} {d['url']} | {d['text'][:150]}")


if __name__ == "__main__":
    corpus = load_docs()
    print(f"Corpus: {len(corpus)} FAQ facts across {len({d['url'] for d in corpus})} URLs; {len(QUERIES)} labeled queries")
    metrics(corpus, 3)
