# Department 3 Final Defect Triage Log
Version: 1.0
Date: 17 November 2026
Overall status: OPEN ITEMS REMAIN — NOT PRODUCTION CLEARED

| ID | Priority | Finding | Evidence / Impact | Status | Required action |
|---|---|---|---|---|---|
| D3-REG-01 | Medium | Four financial use cases skipped | Transaction, budget, multi-period and trend tests lack grounded data access | Blocked | Integrate required financial data retrieval and rerun |
| D3-RET-01 | High | 11 verified-source retrieval misses | Existing live FAQ benchmark matched 30/41 expected sources | Open | Investigate missed questions and source coverage |
| D3-RET-02 | High | Fresh hybrid benchmark unavailable | chunks.json and embeddings.npy missing | Blocked | Restore/rebuild ingestion artifacts and rerun strategy benchmark |
| D3-LAT-01 | Medium | End-to-end latency not measured | Existing 18.47 ms average is retrieval-only | Open | Measure complete API, retrieval, provider and response path |
| D3-CIT-01 | High | Citation accuracy not freshly scored | No answer-level scoring across all 60 questions | Open | Validate citation-to-source correctness |
| D3-UX-01 | High | Multi-turn flows not independently rerun | Complete live financial conversation flows not verified | Open | Execute multi-turn scenarios against integrated service |
| D3-SEC-01 | Critical | Production cross-user isolation unverified | Synthetic isolation test does not establish production isolation | Blocked | Verify authenticated identity propagation and real backend isolation |
| D3-SEC-02 | High | Privacy-related retrieval risk needs verification | Previously identified offline evaluation risk; no confirmed disclosure established | Open | Run adversarial cross-user retrieval and response probes |
| D3-ENV-01 | Low | Pytest asyncio fixture loop scope unset | pytest-asyncio emitted one configuration deprecation warning | Open | Configure asyncio_default_fixture_loop_scope explicitly |
| D3-ENV-02 | Low | Dependency deprecation warnings | Starlette emitted two warnings in final plugin-enabled run | Open | Review dependency upgrades when appropriate |

## Regression execution
Fresh command:
python -m pytest -p pytest_asyncio.plugin -q -rs

Result: 453 passed, 4 skipped, 0 failed, 2 warnings, 31.36 seconds.

## Triage decision
Do not close critical privacy or high grounding/citation issues based only on unit-test success. No confirmed production data leak is asserted. Production clearance requires the blocked end-to-end validations.

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

## Validation Update — 17 November 2026

- Chatbot regression: 28 passed, 0 failed.
- Test-suite duration: 16.08 seconds; this is not end-to-end response latency.
- FAQ follow-up and financial-history privacy tests are covered.
- Inline citation accuracy and production privacy remain open.
- Four data-dependent financial use cases remain skipped.

## Additional Regression Evidence — 17 November 2026

- Chatbot, FAQ RAG, and RAG pipeline regression: 54 passed, 0 failed.
- Test execution duration: 34.72 seconds.
- Verified-source filtering, source metadata, grounded context labels, and existing chatbot behavior tests passed.
- End-to-end inline citation accuracy remains unverified.
- Production source attribution and production user-data isolation remain unverified.
- Status remains PARTIALLY COMPLETE — NOT PRODUCTION CLEARED.

## Fresh Latency Evidence — 17 November 2026

Fresh local FAQ retrieval benchmark completed for 41 verified questions: 35 retrieval successes, 6 empty retrievals, and 30/41 expected-source matches (73.17%). Average latency was 21.23 ms, p50 21.18 ms, p95 24.39 ms, and maximum 25.83 ms.

Classification: MEASURED — LOCAL RETRIEVAL ONLY. Full chatbot/API end-to-end latency and production load performance remain unverified.

## Fresh Five-Strategy Retrieval Benchmark — 17 November 2026

- Fresh benchmark completed: 60 questions; 41 verified scored; 19 unverified excluded.
- Top-3 hit rates: Dense 95.12%, BM25 92.68%, Hybrid RRF 95.12%, Hybrid Metadata 82.93%, Hybrid Metadata + Rerank 85.37%.
- Best MRR: Dense Vector at 0.913.
- Benchmark loaded 12 staged chunks.
- Classification: MEASURED — RETRIEVAL EXPECTED-SOURCE MATCH ONLY.
- Remaining: answer-level failed-query validation, inline citation accuracy, multi-turn financial flows, full chatbot/API latency, and production privacy verification.
