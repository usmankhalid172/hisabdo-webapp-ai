"""
Benchmark XICTEK Systems Blog retrieval against labelled sample queries.

Run from repository root:
    python -m src.xictek_website_assistant.benchmark_retrieval

Uses the persisted TF-IDF index and vectorizer created by ingest.py. No
network access is required. Expected URL fragments are manually labelled
and should be reviewed as the blog content changes.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np

from .config import get_xictek_settings
from .embeddings import embed_query, _vectorizer, _EXPANSION_WEIGHT
from .vector_store import VectorStore

# Labels use URL fragments, not exact ranks. Update these when blog URLs change.
BENCHMARK_QUERIES = [
    {
        "query": "How can I build an AI chatbot for customer conversations?",
        "relevant": ["ai-chatbot-development", "ai-customer-support"],
    },
    {
        "query": "How can a business automate repetitive workflows and tasks?",
        "relevant": ["business-process-automation", "ai-workflow-automation"],
    },
    {
        "query": "How can AI improve ERP systems and business operations?",
        "relevant": ["ai-in-erp-systems"],
    },
    {
        "query": "What should I know about developing mobile apps for a business?",
        "relevant": ["business-mobile-applications", "cross-platform-development", "mobile-app-development-company", "startup-mobile-apps"],
    },
    {
        "query": "How can I create a SaaS platform and scale it?",
        "relevant": ["ai-saas-platforms", "saas-development-services", "saas-product-development"],
    },
    {
        "query": "How do I choose custom software development for my company?",
        "relevant": ["custom-software-development", "custom-software-development-guide"],
    },
    {
        "query": "How can cloud services and Azure support application deployment?",
        "relevant": ["azure-development-services"],
    },
    {
        "query": "How can digital transformation help a company improve processes?",
        "relevant": ["digital-transformation-services", "digital-transformation"],
    },
    {
        "query": "What are the benefits of Flutter and cross-platform app development?",
        "relevant": ["cross-platform-development", "flutter-app-development", "mobile-app-development-company"],
    },
    {
        "query": "How can a company use AI to support small and medium businesses?",
        "relevant": ["ai-for-smes", "ai-development-company-pakistan", "future-of-ai-in-business"],
    },
]


def is_relevant(url: str | None, fragments: list[str]) -> bool:
    url = (url or "").lower()
    return any(fragment.lower() in url for fragment in fragments)


def _normalized_raw_query(text: str) -> np.ndarray:
    """Baseline query vector without synonym expansion."""
    vector = _vectorizer().transform([text]).toarray().astype(np.float32)[0]
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def _evaluate(store: VectorStore, blog_indices: list[int], use_expansion: bool) -> dict:
    top_k = 5
    query_rows, hits_all, precision_all, rr_all, latencies = [], [], [], [], []
    for case in BENCHMARK_QUERIES:
        started = time.perf_counter()
        vector = embed_query(case["query"]) if use_expansion else _normalized_raw_query(case["query"])
        scores = store._vectors[blog_indices] @ vector
        article_scores: dict[str, dict] = {}
        for local_idx, score in zip(blog_indices, scores):
            chunk = store.chunks[local_idx]
            url = chunk.url or ""
            current = article_scores.get(url)
            if current is None or float(score) > current["score"]:
                article_scores[url] = {"title": chunk.title, "url": url, "score": float(score)}
        ranked = sorted(article_scores.values(), key=lambda row: row["score"], reverse=True)[:top_k]
        elapsed_ms = (time.perf_counter() - started) * 1000
        for item in ranked:
            item["score"] = round(item["score"], 4)
            item["relevant"] = is_relevant(item["url"], case["relevant"])
        relevant_ranks = [i for i, item in enumerate(ranked) if item["relevant"]]
        hit = bool(relevant_ranks)
        rr = 1.0 / (relevant_ranks[0] + 1) if hit else 0.0
        hits_all.append(float(hit))
        precision_all.append(len(relevant_ranks) / top_k)
        rr_all.append(rr)
        latencies.append(elapsed_ms)
        query_rows.append({
            "query": case["query"],
            "expected_url_fragments": case["relevant"],
            "hit_at_5": hit,
            "reciprocal_rank": round(rr, 4),
            "latency_ms": round(elapsed_ms, 2),
            "results": ranked,
        })
    return {
        "query_expansion": use_expansion,
        "hit_rate_at_5": round(float(np.mean(hits_all)), 4),
        "precision_at_5": round(float(np.mean(precision_all)), 4),
        "mrr_at_5": round(float(np.mean(rr_all)), 4),
        "mean_retrieval_latency_ms": round(float(np.mean(latencies)), 2),
        "queries": query_rows,
    }


def main() -> None:
    settings = get_xictek_settings()
    store = VectorStore.load()
    if len(store) == 0 or store._vectors is None:
        raise SystemExit(
            "Vector index is missing or empty. Run `python -m "
            "src.xictek_website_assistant.ingest` first from a machine with "
            "network access, then rerun this benchmark."
        )

    blog_indices = [
        i for i, chunk in enumerate(store.chunks)
        if (chunk.url or "").lower().startswith("https://xicteksystems.com/blog/")
    ]
    if not blog_indices:
        raise SystemExit("No XICTEK blog chunks found in the current index.")

    baseline = _evaluate(store, blog_indices, use_expansion=False)
    optimized = _evaluate(store, blog_indices, use_expansion=True)
    report = {
        "website": "https://xicteksystems.com/",
        "scope": "XICTEK Systems /blog/ pages only",
        "embedding_method": "TF-IDF lexical vectors; optimized configuration adds query synonym expansion",
        "embedding_model_setting": settings.embedding_model,
        "synonym_expansion_weight": _EXPANSION_WEIGHT,
        "ranking": "maximum chunk similarity aggregated per article URL",
        "top_k_articles": 5,
        "index_chunks_total": len(store),
        "blog_chunks_evaluated": len(blog_indices),
        "blog_articles_evaluated": len(set(store.chunks[i].url for i in blog_indices)),
        "query_count": len(BENCHMARK_QUERIES),
        "comparison": {
            "baseline_no_query_expansion": {k: v for k, v in baseline.items() if k != "queries"},
            "optimized_with_query_expansion": {k: v for k, v in optimized.items() if k != "queries"},
            "metric_delta_optimized_minus_baseline": {
                metric: round(optimized[metric] - baseline[metric], 4)
                for metric in ("hit_rate_at_5", "precision_at_5", "mrr_at_5")
            },
        },
        # Keep the optimized results at top level for compatibility with the report.
        "hit_rate_at_5": optimized["hit_rate_at_5"],
        "precision_at_5": optimized["precision_at_5"],
        "mrr_at_5": optimized["mrr_at_5"],
        "mean_retrieval_latency_ms": optimized["mean_retrieval_latency_ms"],
        "queries": optimized["queries"],
        "baseline_queries": baseline["queries"],
        "note": (
            "Prototype benchmark, not a production accuracy guarantee. Expected URL fragments are manually labelled. "
            "Uses the checked-in index snapshot; latency excludes application startup and LLM generation."
        ),
    }
    out = Path("xictek_blog_retrieval_benchmark.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("XICTEK Blog Retrieval Benchmark (baseline vs optimized)")
    print(f"Blog chunks: {report['blog_chunks_evaluated']}")
    print(f"Blog articles: {report['blog_articles_evaluated']}")
    print(f"Queries: {report['query_count']}")
    for label, metrics in report["comparison"].items():
        print(f"{label}: {metrics}")
    print(f"Detailed report: {out}")

if __name__ == "__main__":
    main()
