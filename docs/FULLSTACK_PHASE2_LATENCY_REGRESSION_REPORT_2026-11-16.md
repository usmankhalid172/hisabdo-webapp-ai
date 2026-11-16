# Phase 2 Full-Stack Regression, Latency & Throughput Report

**Run date:** 16 November 2026  
**Build under test:** current local checkout on `feature/hassan-hussain-core-services-formatting`  
**Scope:** seven Department 4 website domains; FastAPI chat route, checked-in retrieval index, mock LLM provider, and full repository pytest suite

## Executive summary

- Full repository suite: **397 collected, 393 passed, 4 skipped, 0 failed**. The skips are existing financial-assistant cases blocked on unavailable transaction/budget/history data, not XICTEK website-domain failures.
- Local chat API benchmark: **21 golden source queries × 3 measured repeats = 63 sequential requests**, plus **63 requests at 4 workers** and 21 warmups. HTTP success was 100% for both runs.
- Exact expected-source Hit@8 was **18/21 (85.7%)**, with **MRR@8 0.6619**. All three measured Blog & News source queries missed their expected blog sources; the benchmark showed Core Services routes or no retrieved source for those cases.
- Sequential local TestClient latency: mean **9.304 ms**, p50 **8.990 ms**, p95 **12.378 ms**; throughput **107.097 requests/second**.
- Four-worker local burst: mean per-request latency **35.217 ms**, p50 **34.385 ms**, p95 **46.042 ms**; throughput **112.019 requests/second**.

These are local measurements with the mock LLM and local index. They are not measurements of the deployed service, external network, live LLM generation, production load capacity, or token cost.

## Test execution

The runner executed `pytest -q tests` and wrote JUnit evidence. A stale endpoint test initially assumed the checked-in repository had no index; it failed because the integrated Phase 2 index is present. The test was made deterministic by explicitly injecting an empty vector store for that empty-index scenario. The complete suite then passed: 393 passed, 4 skipped, no failures.

The four skipped tests are pre-existing financial questions requiring live transaction retrieval, budgets, or historical aggregates unavailable to this XICTEK public website assistant. Their skip messages are preserved in `outputs/fullstack_phase2_2026-11-16/pytest_junit.xml`.

## Golden-query and domain results

Hit@8 means at least one expected official source URL appeared in the API's returned `sources` array. For HisabDo offline behavior, `/about`, `/about-app`, and `/faq` were accepted as equivalent expected sources because each contains relevant public offline-use information. MRR is reciprocal rank of the first expected source. This is source retrieval evidence, not claim-level answer entailment.

| Domain | Queries | Hit@8 | MRR@8 | Sequential mean latency |
|---|---:|---:|---:|---:|
| About Us | 3 | 100.0% | 1.0000 | 7.860 ms |
| Core Services | 3 | 100.0% | 0.5833 | 9.473 ms |
| Portfolio & Case Studies | 3 | 100.0% | 1.0000 | 11.759 ms |
| Careers & Job Openings | 3 | 100.0% | 0.8333 | 10.214 ms |
| HisabDo Product | 3 | 100.0% | 0.4833 | 8.187 ms |
| Blog & News | 3 | 0.0% | 0.0000 | 9.349 ms |
| Contact & Locations | 3 | 100.0% | 0.7333 | 8.285 ms |

### Recorded misses

| Case | Observation | Likely failure class |
|---|---|---|
| BLOG-01 | Software-development guide question returned Services chunks | Intent-routing overlap: “software development” is classified as Core Services |
| BLOG-02 | Chatbot/customer-conversation question returned no sources | Retrieval/routing threshold miss; no expected blog source was returned |
| BLOG-03 | SaaS article question returned Services/SaaS Services chunks | Intent-routing overlap: “SaaS” and “product development” route to Core Services |

The misses are retained as failures in the results rather than hidden by changing the expected sources after measurement.

## Baseline versus Phase 2

The repository does **not** contain the exact Day 1 golden-query file or its raw result log. The nearest archived system-wide reference is the 4 November master handover's 85-query offline comparison. It records retrieval hit rising from 50.7% to 87.3%, MRR from 0.41 to 0.83, and context precision from 28.3% to 57.3%. The current run uses a different 21-query set, the checked-in Phase 2 index, top-k 8, and the FastAPI TestClient with a mock generator. Therefore numeric deltas against that archive are shown in the comparison matrix as **directional only; not apples-to-apples**. No defensible Day 1 delta can be claimed without the original dataset and procedure.

## Reproduction and artifacts

Run from the repository root:

```powershell
python scripts/run_phase2_fullstack_regression_benchmark.py
```

The runner writes:

- `outputs/fullstack_phase2_2026-11-16/benchmark_summary.json` — full suite and benchmark summary.
- `outputs/fullstack_phase2_2026-11-16/e2e_latency_source_recall.csv` — case-level results for sequential and concurrent runs.
- `outputs/fullstack_phase2_2026-11-16/pytest_junit.xml` — full-suite test evidence.
- `outputs/fullstack_phase2_2026-11-16/pytest_stdout.txt` and `pytest_stderr.txt` — captured pytest output.

## Environment and interpretation limits

- The benchmark uses local FastAPI `TestClient`, the current checked-in 976-chunk index, and `MockLLMProvider`; no external API calls are made.
- The fitted vectorizer artifact warns that it was created with scikit-learn 1.5.2 and evaluated with 1.7.2. Pin/rebuild before treating small score differences as release-grade.
- 63 requests at four local worker threads are a short smoke burst, not a saturation or production capacity test.
- The archived Day 1 query text was unavailable, so this report does not claim exact matched-set before/after gains.
- No production deployment, real user traffic, live LLM citation correctness, or financial transaction-data workflow was benchmarked.
