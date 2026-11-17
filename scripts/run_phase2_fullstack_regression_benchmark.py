"""Run repository regression tests and a local integrated chat API benchmark.

Run from the repository root:
    python scripts/run_phase2_fullstack_regression_benchmark.py

The end-to-end benchmark uses the checked-in XICTEK index and mock LLM provider.
It measures local FastAPI/TestClient latency, not deployed network/provider latency.
"""
from __future__ import annotations

import csv
import argparse
import json
import os
import statistics
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "fullstack_phase2_2026-11-16"
RUNS_PER_CASE = 3
CONCURRENCY = 4
AUTH_TOKEN = "phase2-regression-local-token"

# Gold sources are canonical URLs present in the checked-in corpus. Queries
# cover the seven Department 4 domains and are intentionally independent of
# generated answer wording; success is source recall at the API boundary.
CASES = [
    {"id":"ABOUT-01","domain":"About Us","query":"Who founded XICTEK Systems?","expected":"https://xicteksystems.com/about"},
    {"id":"ABOUT-02","domain":"About Us","query":"What type of company is XICTEK Systems?","expected":"https://xicteksystems.com/about"},
    {"id":"ABOUT-03","domain":"About Us","query":"How does XICTEK Systems handle client communication?","expected":"https://xicteksystems.com/about"},
    {"id":"SERV-01","domain":"Core Services","query":"What services do you provide for custom software development?","expected":"https://xicteksystems.com/services/custom-software-development"},
    {"id":"SERV-02","domain":"Core Services","query":"What kinds of web applications do you build?","expected":"https://xicteksystems.com/services/web-development"},
    {"id":"SERV-03","domain":"Core Services","query":"Which cloud platforms and Azure services do you support?","expected":"https://xicteksystems.com/services/cloud-solutions"},
    {"id":"PORT-01","domain":"Portfolio & Case Studies","query":"What is HisabDo in the XICTEK portfolio?","expected":"https://xicteksystems.com/portfolio"},
    {"id":"PORT-02","domain":"Portfolio & Case Studies","query":"Which technologies are used to build HisabDo?","expected":"https://xicteksystems.com/portfolio"},
    {"id":"PORT-03","domain":"Portfolio & Case Studies","query":"What outcome does the HisabDo case study report?","expected":"https://xicteksystems.com/portfolio"},
    {"id":"CAREER-01","domain":"Careers & Job Openings","query":"What is the XICTEK internship program?","expected":"https://xicteksystems.com/careers"},
    {"id":"CAREER-02","domain":"Careers & Job Openings","query":"How long is the XICTEK internship program?","expected":"https://xicteksystems.com/careers/internship"},
    {"id":"CAREER-03","domain":"Careers & Job Openings","query":"Who mentors interns at XICTEK Systems?","expected":"https://xicteksystems.com/careers/internship"},
    {"id":"HISABDO-01","domain":"HisabDo Product","query":"What type of app is HisabDo?","expected":"https://hisabdo.app/about"},
    {"id":"HISABDO-02","domain":"HisabDo Product","query":"Does HisabDo work offline?","expected":"https://hisabdo.app/about-app|https://hisabdo.app/about|https://hisabdo.app/faq"},
    {"id":"HISABDO-03","domain":"HisabDo Product","query":"What does a HisabDo customer PDF statement show?","expected":"https://hisabdo.app/about-app"},
    {"id":"BLOG-01","domain":"Blog & News","query":"What does the software development process guide focus on?","expected":"https://xicteksystems.com/blog/software-development-process"},
    {"id":"BLOG-02","domain":"Blog & News","query":"What service does XICTEK offer for customer chatbot conversations?","expected":"https://xicteksystems.com/blog/ai-chatbot-development"},
    {"id":"BLOG-03","domain":"Blog & News","query":"What topics are discussed in the SaaS product development article?","expected":"https://xicteksystems.com/blog/saas-product-development"},
    {"id":"CONTACT-01","domain":"Contact & Locations","query":"What email address can I use to contact XICTEK Systems?","expected":"https://xicteksystems.com/contact"},
    {"id":"CONTACT-02","domain":"Contact & Locations","query":"How can I contact XICTEK about a project?","expected":"https://xicteksystems.com/contact"},
    {"id":"CONTACT-03","domain":"Contact & Locations","query":"Does XICTEK provide post-launch support?","expected":"https://xicteksystems.com/contact"},
]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * p
    lo, hi = int(pos), min(int(pos) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def run_full_pytest(timeout_seconds: int = 120) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    junit = OUT / "pytest_junit.xml"
    command = [sys.executable, "-m", "pytest", "-q", "tests", f"--junitxml={junit}"]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, timeout=timeout_seconds
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        (OUT / "pytest_stdout.txt").write_text(stdout, encoding="utf-8")
        (OUT / "pytest_stderr.txt").write_text(stderr, encoding="utf-8")
        return {
            "status": "TIMED_OUT",
            "timeout_seconds": timeout_seconds,
            "junit_xml": str(junit.relative_to(ROOT)),
        }
    elapsed = time.perf_counter() - started
    (OUT / "pytest_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (OUT / "pytest_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    result = {"exit_code": completed.returncode, "duration_seconds": round(elapsed, 3), "junit_xml": str(junit.relative_to(ROOT))}
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(junit).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        result.update({
            "tests": int(suite.attrib.get("tests", 0)),
            "failures": int(suite.attrib.get("failures", 0)),
            "errors": int(suite.attrib.get("errors", 0)),
            "skipped": int(suite.attrib.get("skipped", 0)),
        })
    except (OSError, ValueError, AttributeError, TypeError):
        result["junit_parse"] = "unavailable"
    return result


def run_api_benchmark() -> tuple[list[dict], dict]:
    os.environ.setdefault("INTERNAL_SERVICE_TOKEN", AUTH_TOKEN)
    os.environ.setdefault("LLM_PROVIDER", "mock")
    os.environ["XICTEK_RATE_LIMIT"] = "10000/minute"
    sys.path.insert(0, str(ROOT))

    from src.xictek_website_assistant import service
    from src.xictek_website_assistant.llm_client import MockLLMProvider
    from src.xictek_website_assistant.schemas import XictekChatRequest

    client = None
    api_mode = False
    api_import_note = None
    try:
        if os.getenv("PHASE2_HANDLER_ONLY") == "1":
            raise ModuleNotFoundError("HTTP mode disabled by PHASE2_HANDLER_ONLY")
        from fastapi.testclient import TestClient
        from src.main import app
        client = TestClient(app)
        api_mode = True
    except ModuleNotFoundError as exc:
        # Preserve useful local retrieval/handler measurements if optional API
        # middleware is unavailable; report clearly that HTTP was not measured.
        api_import_note = f"HTTP API benchmark unavailable: {exc}"

    service._load_store.cache_clear()
    store = service._load_store()
    if len(store) == 0:
        raise RuntimeError("Checked-in vector index is empty; cannot measure source recall")
    service.get_llm_provider = lambda: MockLLMProvider()
    headers = {"X-Internal-Token": os.environ["INTERNAL_SERVICE_TOKEN"]}

    def request_one(case: dict, repeat: int, measure: bool = True) -> dict:
        payload = {
            "message": case["query"],
            "conversation_id": f"phase2-{case['id'].lower()}-{uuid.uuid4().hex[:8]}",
            "history": [],
        }
        start = time.perf_counter()
        if api_mode:
            response = client.post("/api/v1/xictek/chat", json=payload, headers=headers)
            status_code = response.status_code
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        else:
            response = service.handle_chat(XictekChatRequest(**payload))
            status_code = None
            body = response.model_dump()
        latency = (time.perf_counter() - start) * 1000
        sources = body.get("sources", [])
        expected_urls = [url.rstrip("/") for url in case["expected"].split("|")]
        ranks = [i for i, source in enumerate(sources, 1) if source.get("url", "").rstrip("/") in expected_urls]
        return {
            "mode": "sequential", "case_id": case["id"], "domain": case["domain"], "query": case["query"],
            "repeat": repeat, "http_status": status_code if status_code is not None else "NOT_MEASURED",
            "latency_ms": round(latency, 3) if measure else 0.0,
            "expected_source_urls": " | ".join(case["expected"].split("|")),
            "retrieved_source_urls": " | ".join(s.get("url") or "" for s in sources),
            "retrieved_titles": " | ".join(s.get("title") or "" for s in sources),
            "source_hit_at_k": bool(ranks), "reciprocal_rank": 1 / ranks[0] if ranks else 0.0,
            "intent": body.get("intent", ""), "reply_present": bool(body.get("reply")),
            "request_success": bool(body.get("reply")) and (status_code in (None, 200)),
        }

    # Warm the process and local index; exclude warmups from latency metrics.
    for case in CASES:
        request_one(case, 0, measure=False)

    rows = []
    start_all = time.perf_counter()
    for case in CASES:
        for repeat in range(1, RUNS_PER_CASE + 1):
            rows.append(request_one(case, repeat))
    elapsed = time.perf_counter() - start_all

    concurrent_rows = []
    burst_jobs = [(case, repeat) for case in CASES for repeat in range(1, RUNS_PER_CASE + 1)]
    concurrent_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(request_one, case, repeat) for case, repeat in burst_jobs]
        for future in as_completed(futures):
            row = future.result()
            row["mode"] = "concurrent"
            concurrent_rows.append(row)
    concurrent_elapsed = time.perf_counter() - concurrent_started

    latencies = [row["latency_ms"] for row in rows]
    by_domain = {}
    for domain in dict.fromkeys(case["domain"] for case in CASES):
        domain_rows = [row for row in rows if row["domain"] == domain]
        by_domain[domain] = {
            "cases": len({r["case_id"] for r in domain_rows}),
            "requests": len(domain_rows),
            "recall_at_k": round(sum(r["source_hit_at_k"] for r in domain_rows) / len(domain_rows), 4),
            "mrr": round(sum(r["reciprocal_rank"] for r in domain_rows) / len(domain_rows), 4),
            "mean_latency_ms": round(statistics.mean(r["latency_ms"] for r in domain_rows), 3),
            "p95_latency_ms": round(percentile([r["latency_ms"] for r in domain_rows], 0.95), 3),
            "http_success_rate": round(sum(r["http_status"] == 200 for r in domain_rows) / len(domain_rows), 4) if api_mode else None,
        }
    summary = {
        "execution_mode": "FastAPI TestClient endpoint" if api_mode else "direct chat service handler; HTTP layer unavailable",
        "api_import_note": api_import_note,
        "build": "checked-out local repository; mock LLM; checked-in XICTEK index",
        "index_chunk_count": len(store),
        "gold_queries": len(CASES), "repetitions_per_query": RUNS_PER_CASE,
        "measured_requests": len(rows), "warmup_requests": len(CASES),
        "concurrent_requests": len(concurrent_rows), "concurrency_workers": CONCURRENCY,
        "top_k_setting": 8,
        "overall": {
            "http_success_rate": round(sum(r["http_status"] == 200 for r in rows) / len(rows), 4) if api_mode else None,
            "successful_response_rate": round(sum(r["request_success"] for r in rows) / len(rows), 4),
            "recall_at_k": round(sum(r["source_hit_at_k"] for r in rows) / len(rows), 4),
            "mrr": round(sum(r["reciprocal_rank"] for r in rows) / len(rows), 4),
            "mean_latency_ms": round(statistics.mean(latencies), 3),
            "p50_latency_ms": round(percentile(latencies, 0.50), 3),
            "p95_latency_ms": round(percentile(latencies, 0.95), 3),
            "max_latency_ms": round(max(latencies), 3),
            "sequential_throughput_req_per_sec": round(len(rows) / elapsed, 3),
            "elapsed_seconds": round(elapsed, 3),
        },
        "concurrent_burst": {
            "requests": len(concurrent_rows),
            "concurrency_workers": CONCURRENCY,
            "http_success_rate": round(sum(r["http_status"] == 200 for r in concurrent_rows) / len(concurrent_rows), 4) if api_mode else None,
            "successful_response_rate": round(sum(r["request_success"] for r in concurrent_rows) / len(concurrent_rows), 4),
            "recall_at_k": round(sum(r["source_hit_at_k"] for r in concurrent_rows) / len(concurrent_rows), 4),
            "mrr": round(sum(r["reciprocal_rank"] for r in concurrent_rows) / len(concurrent_rows), 4),
            "mean_latency_ms": round(statistics.mean(r["latency_ms"] for r in concurrent_rows), 3),
            "p50_latency_ms": round(percentile([r["latency_ms"] for r in concurrent_rows], 0.50), 3),
            "p95_latency_ms": round(percentile([r["latency_ms"] for r in concurrent_rows], 0.95), 3),
            "max_latency_ms": round(max(r["latency_ms"] for r in concurrent_rows), 3),
            "throughput_req_per_sec": round(len(concurrent_rows) / concurrent_elapsed, 3),
            "elapsed_seconds": round(concurrent_elapsed, 3),
        },
        "domains": by_domain,
        "limits": [
            "Local execution only; does not include deployed host, network, or production load-balancer latency.",
            "Mock provider; no live LLM generation time, token cost, or citation-quality scoring.",
            "Recall@k is exact expected source URL presence in API sources, not passage entailment.",
            "Sequential throughput is not a concurrent capacity/load test.",
        ],
    }
    return rows + concurrent_rows, summary


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUT,
        help="Directory for JUnit, latency, and benchmark output (default: prior Phase 2 output folder).",
    )
    parser.add_argument(
        "--benchmark-only",
        action="store_true",
        help="Skip repository pytest and run only the domain query/latency benchmark.",
    )
    parser.add_argument(
        "--handler-only",
        action="store_true",
        help="Benchmark the local chat handler directly instead of the HTTP TestClient layer.",
    )
    parser.add_argument(
        "--pytest-timeout-seconds",
        type=int,
        default=120,
        help="Maximum seconds allowed for the full pytest suite before the benchmark continues (default: 120).",
    )
    parser.add_argument(
        "--min-recall-at-k",
        type=float,
        default=1.0,
        help="Minimum expected-source Recall@k required for a successful exit (default: 1.0).",
    )
    args = parser.parse_args()
    OUT = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    OUT.mkdir(parents=True, exist_ok=True)
    if args.handler_only:
        os.environ["PHASE2_HANDLER_ONLY"] = "1"
    pytest = (
        {"status": "SKIPPED_BY_OPTION"}
        if args.benchmark_only
        else run_full_pytest(timeout_seconds=args.pytest_timeout_seconds)
    )
    rows, benchmark = run_api_benchmark()
    with (OUT / "e2e_latency_source_recall.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "benchmark_summary.json").write_text(json.dumps({
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pytest": pytest,
        "benchmark": benchmark,
    }, indent=2), encoding="utf-8")
    print(json.dumps({"pytest": pytest, "benchmark": benchmark}, indent=2))
    success_rate = benchmark["overall"]["successful_response_rate"]
    recall_at_k = benchmark["overall"]["recall_at_k"]
    pytest_ok = args.benchmark_only or pytest.get("exit_code") == 0
    return 0 if pytest_ok and success_rate == 1.0 and recall_at_k >= args.min_recall_at_k else 1


if __name__ == "__main__":
    raise SystemExit(main())
