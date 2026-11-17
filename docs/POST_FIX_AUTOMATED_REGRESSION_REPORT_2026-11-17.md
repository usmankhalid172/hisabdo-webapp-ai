# Post-Fix Automated Regression Report

**Date:** 17 November 2026  
**Branch:** `feature/hassan-hussain-core-services-formatting`  
**Revision tested:** `1531a68`  
**Environment:** local checkout, checked-in XICTEK index, mock LLM provider

## Executive result

The domain response benchmark completed, but the release cannot be signed off as regression-free. It found three repeatable Blog & News source-retrieval misses. The complete repository pytest suite did not finish: execution stalled at the first integration test, `tests/integration/test_ai_integration.py::test_valid_chat_request_is_processed`. The run was stopped before pytest produced a JUnit report. Therefore, this report does **not** claim zero open regressions or a complete passing test suite.

The 21-query benchmark was rerun through the local chat service handler (not through HTTP), using 3 measured repetitions per query and a 4-worker concurrent burst. All 63 sequential and 63 concurrent requests returned a reply. Overall expected-source Recall@8 was 54/63 (85.71%), with MRR 0.6619. The test uses a mock LLM and does not validate generated answer truthfulness or production latency.

## Results by domain

| Domain | Queries | Source hits | Recall@8 | MRR | Result |
|---|---:|---:|---:|---:|---|
| About Us | 3 | 9/9 repeated requests | 100% | 1.0000 | Pass |
| Core Services | 3 | 9/9 | 100% | 0.5833 | Source found; ranking needs review |
| Portfolio & Case Studies | 3 | 9/9 | 100% | 1.0000 | Pass |
| Careers & Job Openings | 3 | 9/9 | 100% | 0.8333 | Source found; ranking needs review |
| HisabDo Product | 3 | 9/9 | 100% | 0.4833 | Source found; ranking needs review |
| Blog & News | 3 | 0/9 | 0% | 0.0000 | **Fail: all three queries missed the expected blog source** |
| Contact & Locations | 3 | 9/9 | 100% | 0.7333 | Source found; ranking needs review |

Each query was measured three times sequentially and three times in the concurrent burst. Per-domain latency and source-level details are in the CSV artifact. The first retrieved expected source is reflected in MRR; a hit anywhere within the configured top 8 counts for Recall@8.

## Open failures

| Case | Query | Observed retrieval | Finding |
|---|---|---|---|
| BLOG-01 | What does the software development process guide focus on? | Custom software development/service pages | Wrong domain pages outrank/mask the expected blog article. |
| BLOG-02 | What service does XICTEK offer for customer chatbot conversations? | No source chunks | Query returns a general fallback without retrieved evidence. |
| BLOG-03 | What topics are discussed in the SaaS product development article? | Services and SaaS service pages | Expected blog article is not retrieved. |

These are open retrieval failures, not evidence of hallucinations: the benchmark checks source URL retrieval and reply presence, not whether the generated text is factually entailed. Fix the blog routing/filtering or query-to-section selection, then rerun these cases and the full suite before release clearance.

## Suite execution status

- Pytest collected **397 tests** successfully.
- The full test run stalled at the first integration test and was stopped; no trustworthy pass/fail totals or JUnit artifact were produced.
- A XICTEK-focused subset also stalled during execution and did not produce a JUnit result.
- The benchmark runner exited with code `1` because measured Recall@8 (85.71%) is below its default release gate of 100%; this is the expected failure signal for the three Blog & News misses.
- `scripts/production_smoke_test.py` passed Python bytecode compilation and its `--help` invocation.
- No production smoke test was run. An approved production URL and secure service token were not supplied. The local API did not become ready during the attempted smoke-test setup, so no local endpoint pass is claimed either.

The regression runner now supports `--pytest-timeout-seconds` so a future full run records a timeout instead of waiting indefinitely. Its `--benchmark-only --handler-only` options reproduce the completed local domain benchmark without misrepresenting handler measurements as HTTP measurements.

## Benchmark summary

- Corpus: 976 indexed chunks.
- Retrieval setting: top-k 8.
- Queries: 21 unique, 3 per domain.
- Sequential measured requests: 63; reply rate 100%; mean 3.210 ms; p95 5.319 ms.
- Concurrent measured requests: 63 at 4 workers; reply rate 100%; mean 13.627 ms; p95 36.204 ms.
- Throughput in this local direct-handler run: 308.351 sequential requests/second and 280.596 concurrent requests/second. These are not HTTP or production capacity measurements.

## Artifacts

- `outputs/postfix_regression_2026-11-17/benchmark_summary.json` — machine-readable summary.
- `outputs/postfix_regression_2026-11-17/e2e_latency_source_recall.csv` — per-query run details and retrieved URLs.
- `outputs/postfix_regression_2026-11-17/benchmark_console.txt` — benchmark execution output.
- `docs/PRODUCTION_SMOKE_TEST_EXECUTION_GUIDE_2026-11-17.md` — smoke-test instructions and release execution requirements.

## Release decision

**Not cleared for release by this verification.** Blog & News has three reproducible source misses, full pytest completion is unverified, and production smoke checks remain to be run against the approved deployment. The remaining domains achieved 100% source hit rate on this small 3-query-per-domain set; that is useful evidence but not proof of zero regressions.
