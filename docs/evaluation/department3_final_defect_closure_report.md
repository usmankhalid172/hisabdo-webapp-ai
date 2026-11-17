# Department 3 Final Defect Closure Report

**Project:** HisabDo Expense Management Chatbot  
**Department:** 3  
**Report status:** Submission-ready; production clearance pending  
**Prepared:** 17 November 2026

## 1. Executive Summary

The Day 8 defect triage findings were reviewed against the current source code, tests, and available ingestion artifacts. Retriever input-validation edge cases were hardened, and a regression test was added to ensure FAQ response context preserves citation metadata.

The focused regression suite completed successfully: **31 passed, 0 failed**. Two dependency deprecation warnings remain. This report distinguishes locally verified fixes from issues that require production infrastructure or additional evidence.

**Overall disposition: PARTIALLY COMPLETE ? NOT PRODUCTION CLEARED.**

## 2. Defect Closure Matrix

| Defect | Severity | Current disposition | Evidence / remaining action |
|---|---|---|---|
| D3-REG-01: Financial use-case tests skipped | Medium | Open / blocked | Four data-dependent use cases remain skipped: transaction, budget, multi-period comparison, trends/aggregates. Require grounded backend data and rerun. |
| D3-RET-01: Verified-source retrieval misses | High | Open | Historical benchmark: 30/41 expected-source matches. Review missing questions and source coverage; do not treat retrieval hit rate as answer accuracy. |
| D3-RET-02: Hybrid benchmark/index artifacts | High | Partially addressed | Local ingestion artifacts are present. Active chatbot path uses dense in-memory retrieval; no production hybrid deployment or approved hybrid weights established. Rebuild and benchmark before any hybrid rollout. |
| D3-LAT-01: End-to-end latency unavailable | Medium | Open / blocked | Retrieval-only timing exists; production end-to-end latency requires real backend and deployed environment. |
| D3-CIT-01: Citation accuracy not freshly scored | High | Open | Citation metadata preservation regression test added. Semantic answer-to-source accuracy across the full benchmark remains unverified. |
| D3-UX-01: Multi-turn flows not independently rerun | High | Open | Requires dedicated multi-turn scenarios and evidence. |
| D3-SEC-01: Production cross-user isolation | Critical | Open / release blocker | Synthetic tests are not proof of production isolation. Real backend and trusted identity propagation must be validated. |
| D3-SEC-02: Privacy-related retrieval risk | High | Open / release blocker | Run adversarial cross-user probes against the real authenticated backend before closure. |
| D3-ENV-01: Async fixture loop warning | Low | Fixed locally | Added explicit `asyncio_default_fixture_loop_scope = function` in pytest.ini. Verify with the full suite. |
| D3-ENV-02: Starlette dependency warnings | Low | Deferred | Warnings originate from installed Starlette/AnyIO compatibility. Review dependency upgrades in a controlled compatibility test; no unverified upgrade applied. |
| Retriever invalid input limits | Low | Fixed locally | Both secondary retrievers now reject invalid `top_k`; FinancialRetriever also rejects non-string/blank queries and invalid/non-finite/out-of-range `min_score`. |
| FAQ context citation metadata loss | Medium | Fixed locally | FAQ helper now preserves ID, title, source URL, section, score, and verified status. Regression test added. |

## 3. Verification Evidence

Focused command:

`python -m pytest tests/test_retrieval.py tests/test_faq_rag.py tests/test_rag_pipeline.py -q`

Result: **31 passed, 0 failed, 2 warnings**.

The FAQ RAG regression suite verifies that unverified documents are excluded and verified source metadata is retained. The new pipeline regression test verifies that citation metadata survives the FAQ helper path.

Previously recorded Day 8 evidence:
- Full suite (final verification, 17 November 2026): 456 passed, 4 skipped, 0 failed, 2 dependency warnings (74.92 seconds).
- Retrieval benchmark: 41 verified questions scored; Dense top-3 hit rate 95.12%, BM25 92.68%, Hybrid RRF 95.12%, Hybrid Metadata 82.93%, Hybrid Metadata + Rerank 85.37%.
- Historical retrieval execution: 30/41 expected-source matches (73.17%), average 21.23 ms, p95 24.39 ms.

These are historical local measurements. Expected-source retrieval matching is not answer-level citation accuracy or production latency.

## 4. Release Blockers and Required Evidence

Production release remains blocked until:
1. Real backend integration replaces the mock backend and financial data access is tested.
2. Trusted authenticated identity is propagated and verified end-to-end.
3. Cross-user isolation and adversarial privacy probes pass against the real backend.
4. Citation accuracy and multi-turn flows are independently evaluated.
5. Four skipped financial use cases are executed with grounded data.
6. End-to-end latency and production monitoring are measured.

## 5. Final Disposition

Local low-severity retriever validation and citation metadata preservation fixes are implemented and focused tests pass. The pytest fixture loop scope is explicitly configured. Dependency warnings and production-dependent defects remain documented.

**Final status: PARTIALLY COMPLETE ? NOT PRODUCTION CLEARED.**
