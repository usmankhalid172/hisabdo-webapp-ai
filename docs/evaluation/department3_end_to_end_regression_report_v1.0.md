# Department 3 End-to-End Regression Report
Version: 1.0
Status: PARTIALLY COMPLETE — NOT PRODUCTION CLEARED
Date: 17 November 2026

## 1. Objective
Evaluate the HisabDo financial assistant regression status across automated tests, retrieval evidence, latency, grounding, conversational safety and privacy boundaries.

## 2. Fresh Automated Regression
Command:
python -m pytest -p pytest_asyncio.plugin -q -rs

Result:
- Passed: 453
- Skipped: 4
- Failed: 0
- Warnings: 2
- Runtime: 31.36 seconds

The four skipped tests are blocked by unavailable grounded data capabilities:
1. Transaction-level answers
2. Budget answers
3. Multi-period comparisons
4. Trend/aggregate insights

The async tests executed successfully after explicitly loading pytest-asyncio.

## 3. Historical Day 1 Baseline
The previously documented 19-question exploratory baseline recorded:
- 11 clear passes
- 6 retrieval issues
- 1 partial response
- 1 backend limitation

This is historical evidence, not a fresh rerun of the same 19 questions.

## 4. Retrieval Evaluation Evidence
Existing 60-question evaluation dataset:
- 41 questions with verified expected sources
- 17 questions without verified expected sources
- 2 questions without expected sources
- Existing live FAQ retrieval: 30/41 expected-source matches (73.17%)
- 11 verified-source misses
- 13 safe abstentions
- 6 manual review cases

Existing staged retrieval benchmark:
- MATCH: 28
- MISS: 13
- SAFE_ABSTENTION: 11
- REVIEW: 8
- In-scope expected-source match: 28/41 (68.29%)

The staged-vector benchmark is not directly comparable to the historical live FAQ retriever benchmark.

## 5. Retrieval Strategy Evidence
Previously generated strategy results show:
- Hybrid RRF, top-5: 40/41 expected-source hits (97.56%)
- Hybrid RRF, top-3: 39/41 (95.12%)
- Dense vector, top-5: 39/41 (95.12%)

These are existing saved benchmark outputs. They were not regenerated during this validation because data/ingestion/chunks.json and data/ingestion/embeddings.npy were missing.

## 6. Latency
Existing local FAQ retrieval benchmark:
- Average: 18.47 ms
- Median (p50): 18.47 ms
- p95: 21.07 ms
- Maximum: 21.37 ms
- Successful retrievals: 35
- Empty retrievals: 6

This measures local retrieval only. It does not measure complete chatbot response latency, external LLM/API latency, or production load.

## 7. Grounding, Citations and Privacy
Automated regression passed, but a passing test suite alone does not establish end-to-end citation correctness or production privacy isolation.

Previously documented limitations:
- Production financial backend and production secret were not available for verification.
- Synthetic isolation testing is not proof of real production cross-user isolation.
- A previously identified retrieval privacy risk requires end-to-end verification; it is not evidence of a confirmed customer data disclosure.
- Multi-turn financial flows and adversarial probes have not been independently executed as a complete live end-to-end test set in this run.
- Inline citation accuracy across all 60 questions has not been freshly scored.

## 8. Before-versus-After Conclusion
The fresh automated suite has 453 passing tests and zero failures. However, the 19-question historical exploratory baseline and the current broad pytest suite are different test populations. Therefore, a numerical improvement percentage in chatbot answer quality cannot be claimed.

The existing retrieval evidence provides useful strategy comparisons, but the missing ingestion artifacts prevented a fresh hybrid retrieval benchmark.

## 9. Final Decision
PARTIALLY COMPLETE — NOT PRODUCTION CLEARED.

Completed:
- Fresh automated regression suite
- Async test execution
- Historical baseline review
- Existing retrieval and latency evidence review
- Benchmark limitations documented

Pending:
- Rebuild or restore current ingestion chunks and embeddings
- Fresh golden-question and failed-query benchmark
- Independent multi-turn financial flow execution
- Adversarial privacy and safety probes
- Inline citation accuracy scoring
- Real backend and cross-user isolation validation
- Full end-to-end response latency measurement

No production readiness or zero-regression claim is made.

## Latest Validation Update — 17 November 2026

### Confirmed Automated Results
- Full regression suite: 453 passed, 4 skipped, 0 failed.
- Chatbot tests: 28 passed, 0 failed.
- Security/API/isolation tests: 54 passed, 0 failed.
- Adversarial/multilingual/retrieval/use-case tests: 34 passed, 4 skipped, 0 failed.
- Four skipped use cases require data retrieval/grounded historical data.
- Two deprecation warnings were reported in the latest chatbot test run.

### Remaining Validation Gaps
- Live production backend connection and trusted production identity are not verified.
- Dedicated multi-turn financial flow tests were not found; multi-turn validation remains untested.
- Inline citation accuracy is not fully verified.
- End-to-end chatbot latency and a directly comparable before/after quality benchmark remain pending.
- Synthetic/mock isolation tests do not prove production customer-data isolation.

### Final Assessment
PARTIALLY COMPLETE — NOT PRODUCTION CLEARED.
Automated regression tests passed. Outstanding integration, multi-turn, citation, and production verification gaps must remain open. No production-safety or zero-regression claim is made beyond the tests actually executed.

## Additional Validation — 17 November 2026

- Chatbot regression suite rerun: 28 passed, 0 failed.
- Total test-suite duration: 16.08 seconds.
- Slowest test: unrelated-query general fallback (15.88 seconds).
- Endpoint response-shape test: 0.02 seconds.
- Two dependency deprecation warnings remain.
- These timings are test execution timings, not measured end-to-end user response latency.
- Existing tests cover verified FAQ retrieval, source conflict handling, unverified-source exclusion, FAQ follow-up context, and protection against reusing personal or third-party financial questions.
- Inline citation correctness still requires a dedicated end-to-end response-level benchmark.

## Additional RAG and Citation-Related Regression — 17 November 2026

- Test suites: test_chatbot.py, test_faq_rag.py, test_rag_pipeline.py
- Result: 54 passed, 0 failed.
- Duration: 34.72 seconds.
- Warnings: 2 dependency deprecation warnings.
- Verified and unverified FAQ retrieval behavior, source metadata, grounded context labels, and chatbot response behavior passed their existing tests.
- Limitation: This test run does not establish end-to-end inline citation accuracy or production source attribution.

## Fresh Local FAQ Retrieval Benchmark — 17 November 2026

- Verified questions measured: 41
- Retrieval successes: 35
- Empty retrievals: 6
- Expected-source matches: 30/41 (73.17%)
- Average latency: 21.23 ms
- Median latency (p50): 21.18 ms
- p95 latency: 24.39 ms
- Maximum latency: 25.83 ms

Scope limitation: This is a local FAQ retrieval benchmark, not full chatbot/API end-to-end latency, answer accuracy, or a load test.

## Fresh Five-Strategy Retrieval Benchmark — 17 November 2026

- Total questions: 60
- Verified questions scored: 41
- Unverified questions excluded: 19
- Historical baseline MISS rows: 11
- Dense Vector Top-3: 95.12%, MRR 0.913
- BM25 Lexical Top-3: 92.68%, MRR 0.826
- Hybrid RRF Top-3: 95.12%, MRR 0.8882
- Hybrid Metadata Top-3: 82.93%, MRR 0.7602
- Hybrid Metadata + Rerank Top-3: 85.37%, MRR 0.7724

Scope: Expected-source retrieval hit rate and MRR only. These results do not establish answer accuracy, citation correctness, or end-to-end chatbot performance. Benchmark loaded 12 staged chunks.
