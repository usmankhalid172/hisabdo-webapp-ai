"""Compare current HisabDo cosine retrieval with a source-metadata filter.

Run from the repository root:
    python scripts/evaluate_hisabdo_retrieval.py

This evaluates the checked-in local index only. The Day 1 prompts were not
included verbatim in the repository, so cases are representative proxies
derived from the recorded FV-01..FV-06 failure/partial descriptions.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.xictek_website_assistant.embeddings import embed_query

INDEX = ROOT / "src/xictek_website_assistant/data/index"
DOCS = ROOT / "docs"
QUERY_LOG = DOCS / "HISABDO_RETRIEVAL_QUERY_LOG_2026-11-11.csv"
CALIBRATION = DOCS / "HISABDO_RETRIEVAL_THRESHOLD_CALIBRATION_2026-11-11.csv"

# Canonical, first-party product/help URLs; blog/career/profile routes are
# intentionally excluded from this product-feature filter.
PRODUCT_PATHS = {
    "/", "/about", "/about-app", "/app", "/faq", "/privacy-policy",
}

CASES = [
    {
        "id": "FV-01",
        "area": "Product overview",
        "query": "What is HisabDo and what business problem does it solve?",
        "expected_paths": {"/", "/about", "/about-app", "/app", "/faq"},
    },
    {
        "id": "FV-02",
        "area": "Guest mode",
        "query": "Can I use HisabDo without creating an account?",
        "expected_paths": {"/", "/about", "/about-app", "/app", "/faq"},
    },
    {
        "id": "FV-03",
        "area": "Offline feature coverage",
        "query": "Which HisabDo features can I use offline without internet?",
        "expected_paths": {"/", "/about", "/about-app", "/app", "/faq"},
    },
    {
        "id": "FV-04",
        "area": "Sign-in synchronization boundary",
        "query": "When I sign in, are my existing local records uploaded, merged, or replaced?",
        "expected_paths": {"/faq", "/privacy-policy"},
    },
    {
        "id": "FV-05",
        "area": "Customer management",
        "query": "Can I manage customer balances and see each customer's transaction history?",
        "expected_paths": {"/about", "/about-app", "/app", "/faq"},
    },
    {
        "id": "FV-06",
        "area": "PDF report contents",
        "query": "What information is included in HisabDo PDF reports or statements?",
        "expected_paths": {"/about", "/about-app", "/app", "/faq"},
    },
]

THRESHOLDS = (0.0, 0.05, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30)
TOP_K_VALUES = (3, 5, 8)


def _url_metadata(url: str | None) -> tuple[str, str]:
    parsed = urlsplit(url or "")
    host = (parsed.hostname or "").casefold().removeprefix("www.")
    path = parsed.path.rstrip("/").casefold() or "/"
    return host, path


def _metadata_eligible(chunk: dict) -> bool:
    host, path = _url_metadata(chunk.get("url"))
    return host == "hisabdo.app" and path in PRODUCT_PATHS


def _rank(scores: np.ndarray, candidates: np.ndarray, threshold: float, top_k: int) -> list[int]:
    candidates = candidates[scores[candidates] >= threshold]
    if not len(candidates):
        return []
    return candidates[np.argsort(-scores[candidates], kind="stable")[:top_k]].tolist()


def _evaluate_one(case: dict, chunks: list[dict], scores: np.ndarray, candidates: np.ndarray,
                  threshold: float, top_k: int, method: str) -> dict:
    indices = _rank(scores, candidates, threshold, top_k)
    returned = [chunks[i] for i in indices]
    returned_pages = {
        (host, path)
        for host, path in (_url_metadata(c.get("url")) for c in returned)
    }
    relevant_pages = {
        page for page in returned_pages
        if page[0] == "hisabdo.app" and page[1] in case["expected_paths"]
    }
    expected_pages = {("hisabdo.app", path) for path in case["expected_paths"]}
    expected_paths = sorted(case["expected_paths"])
    matched_paths = sorted(path for host, path in relevant_pages if host == "hisabdo.app")
    return {
        "case_id": case["id"],
        "area": case["area"],
        "query": case["query"],
        "method": method,
        "threshold": threshold,
        "top_k": top_k,
        "returned_count": len(returned),
        "hit": bool(relevant_pages),
        "unique_source_precision": len(relevant_pages) / len(returned_pages) if returned_pages else 0.0,
        "expected_source_coverage": len(relevant_pages) / len(expected_pages),
        "expected_paths": " | ".join(expected_paths),
        "matched_expected_paths": " | ".join(matched_paths),
        "top_sources": " | ".join(
            f"{c.get('title','')} ({c.get('url','')}) score={scores[i]:.4f}"
            for i, c in zip(indices, returned)
        ),
        "top_paths": " | ".join(f"{_url_metadata(c.get('url'))[0]}{_url_metadata(c.get('url'))[1]}"
                                 for c in returned),
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    chunks = json.loads((INDEX / "chunks.json").read_text(encoding="utf-8"))
    vectors = np.load(INDEX / "embeddings.npy")
    if len(chunks) != vectors.shape[0]:
        raise SystemExit(f"Index mismatch: {len(chunks)} chunks vs {vectors.shape[0]} vectors")

    metadata = json.loads((INDEX / "metadata.json").read_text(encoding="utf-8"))
    model_label = metadata.get("embedding_model", "unknown")
    metadata_candidates = np.array(
        [i for i, chunk in enumerate(chunks) if _metadata_eligible(chunk)], dtype=int
    )
    all_candidates = np.arange(len(chunks), dtype=int)
    results: list[dict] = []

    for case in CASES:
        query_vector = embed_query(case["query"])
        if query_vector.shape[0] != vectors.shape[1]:
            raise SystemExit(
                f"Query/index dimension mismatch ({query_vector.shape[0]} vs {vectors.shape[1]}); "
                "do not compare incompatible vector spaces."
            )
        scores = vectors @ query_vector
        for method, candidates in (
            ("baseline_all_chunks", all_candidates),
            ("metadata_product_pages", metadata_candidates),
        ):
            for top_k in TOP_K_VALUES:
                for threshold in THRESHOLDS:
                    results.append(
                        _evaluate_one(case, chunks, scores, candidates, threshold, top_k, method)
                    )

    calibration: list[dict] = []
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for result in results:
        grouped[(result["method"], result["top_k"], result["threshold"])].append(result)

    for (method, top_k, threshold), group in sorted(grouped.items()):
        calibration.append({
            "method": method,
            "top_k": top_k,
            "cosine_threshold": threshold,
            "cases": len(group),
            "query_hit_count": sum(row["hit"] for row in group),
            "hit_rate": round(sum(row["hit"] for row in group) / len(group), 4),
            "mean_unique_source_precision": round(
                sum(row["unique_source_precision"] for row in group) / len(group), 4
            ),
            "mean_expected_source_coverage": round(
                sum(row["expected_source_coverage"] for row in group) / len(group), 4
            ),
            "no_result_count": sum(row["returned_count"] == 0 for row in group),
        })

    # Choose the highest hit rate, then precision, then fewer returned rows,
    # then the stricter threshold. Small sample size means this is calibration,
    # not a production guarantee.
    selected: dict[str, tuple[int, float]] = {}
    for method in ("baseline_all_chunks", "metadata_product_pages"):
        options = [r for r in calibration if r["method"] == method]
        best = max(options, key=lambda r: (
            r["hit_rate"], r["mean_unique_source_precision"],
            r["mean_expected_source_coverage"], -r["no_result_count"],
            r["cosine_threshold"], -r["top_k"],
        ))
        selected[method] = (best["top_k"], best["cosine_threshold"])

    query_log: list[dict] = []
    for case in CASES:
        query_vector = embed_query(case["query"])
        scores = vectors @ query_vector
        for method, candidates in (
            ("baseline_all_chunks", all_candidates),
            ("metadata_product_pages", metadata_candidates),
        ):
            top_k, threshold = selected[method]
            query_log.append(
                _evaluate_one(case, chunks, scores, candidates, threshold, top_k, method)
            )

    _write_csv(CALIBRATION, calibration)
    _write_csv(QUERY_LOG, query_log)
    print(f"index_chunks={len(chunks)} vectors={vectors.shape} model_metadata={model_label}")
    print(f"metadata_product_page_chunks={len(metadata_candidates)}")
    for method, (top_k, threshold) in selected.items():
        row = next(r for r in calibration if r["method"] == method
                   and r["top_k"] == top_k and r["cosine_threshold"] == threshold)
        print(
            f"{method}: top_k={top_k} threshold={threshold:.2f} "
            f"hit_rate={row['hit_rate']:.3f} "
            f"mean_unique_source_precision={row['mean_unique_source_precision']:.3f} "
            f"no_results={row['no_result_count']}"
        )
    print(f"query_log={QUERY_LOG}")
    print(f"threshold_calibration={CALIBRATION}")


if __name__ == "__main__":
    main()
