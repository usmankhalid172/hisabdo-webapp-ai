# Department 3 - Final Evaluation Scorecard

**Project:** HisabDo Expense Management Chatbot  
**Department:** Department 3 - Expense Management  
**Report Version:** 1.1  
**Evaluation Date:** 5 November 2026  
**Status:** PARTIALLY COMPLETE  
**Production Release:** BLOCKED - Pending Backend and Production Security Verification

## 1. Evaluation Scope

This evaluation covers the Department 3 chatbot's knowledge retrieval, authentication controls, automated regression tests, synthetic user-isolation testing, monitoring, and financial-data safety.

The evaluation uses:

- 60-question Department 3 evaluation dataset.
- Verified FAQ retrieval results.
- Automated project test suite.
- Authentication and API security checks.
- Synthetic two-user service-level isolation test.
- Existing local retrieval latency benchmark.

## 2. Evaluation Dataset Summary

| Dataset Category | Questions |
|---|---:|
| Verified | 41 |
| Unverified | 17 |
| No verified source | 2 |
| **Total** | **60** |

No real customer financial records were included in the evaluation dataset.

## 3. Retrieval Evaluation Results

| Retrieval Outcome | Questions |
|---|---:|
| MATCH | 30 |
| MISS | 11 |
| SAFE_ABSTENTION | 13 |
| REVIEW | 6 |
| **Total** | **60** |

Expected-source match rate:

**30 / 41 x 100 = 73.17%**

This measures expected knowledge-base source retrieval, not chatbot answer accuracy.

## 4. Automated Test Results

Command executed:

`python -m pytest -q -rs`

Latest result on 5 November 2026:

| Metric | Result |
|---|---:|
| Passed | 408 |
| Failed | 0 |
| Skipped | 4 |
| Warnings | 2 |
| Execution time | 52.73 seconds |

The four skipped tests concern:

- Transaction-level answers.
- Budget answers.
- Multi-period comparisons.
- Financial trends and insights.

These use cases require financial-data retrieval capabilities not currently available in the tested layer.

The two warnings concern dependency deprecations, not test failures.

A new synthetic user-isolation test was added:

`tests/test_department3_user_isolation.py`

Command executed:

`python -m pytest tests\test_department3_user_isolation.py -v`

Result: **1 passed, 0 failed.**

The test verified that two synthetic user IDs were passed separately to the backend client and that each user's synthetic financial context excluded the other user's unique balance marker.

## 5. Authentication Security Results

Actual authentication dependency checks were previously executed without the test authentication override.

| Test Case | Expected | Actual | Result |
|---|---:|---:|---|
| Missing internal token | 401 | 401 | PASS |
| Incorrect internal token | 401 | 401 | PASS |
| Missing authenticated user ID | 401 | 401 | PASS |
| Valid configured credentials | 200 | 200 | PASS |

**Result: 4/4 checks passed.**

The configured internal token is a development placeholder. Successful local authentication checks do not establish production authentication readiness.

## 6. Retrieval Latency

Existing local FAQ retrieval benchmark:

| Metric | Result |
|---|---:|
| Successful retrievals | 35 |
| Empty retrievals | 6 |
| Average latency | 18.47 ms |
| Median latency | 18.47 ms |
| p95 latency | 21.07 ms |
| Maximum latency | 21.37 ms |

These figures measure local FAQ retrieval only. They do not represent complete chatbot response time, provider latency, or production load performance.

## 7. Financial Data Security Assessment

Verified implementation findings:

- Chatbot API requests require internal service authentication.
- The authenticated user identity must match the request user ID.
- A mismatch is rejected with HTTP 403.
- Missing or invalid internal tokens are rejected.
- Missing authenticated user IDs are rejected.
- The service passes the request user ID to `get_user_financial_summary`.
- The current backend client is a MockBackendClient that fails safely with HTTP 503 rather than returning fabricated financial figures.
- The synthetic two-user service-level isolation test passed.

Not yet verified:

- Real authenticated financial backend integration.
- Production identity derivation from a trusted login/session.
- Cross-user data isolation using real backend accounts.
- Production secret configuration.
- Production end-to-end financial request behavior.
- Production zero-data-leakage under concurrent or separate real user sessions.

The synthetic test verifies service-level user-ID propagation and context separation only. It does not prove isolation inside a real backend or production environment.

Therefore, zero cross-user data leakage under production conditions is **NOT VERIFIED**.

## 8. Seven-Dimension Response Quality Evaluation

The scoring rubric defines seven dimensions:

1. Factual accuracy.
2. Relevance.
3. Completeness.
4. Citation correctness.
5. Clarity.
6. Language.
7. Safety.

Each dimension is scored from 0 to 4, for a maximum of 28 points per response.

The 60-question retrieval dataset has not yet been evaluated through actual chatbot response generation and scoring.

Therefore, final response accuracy, completeness, citation correctness, and overall response-quality percentages are not available.

## 9. Overall Evaluation Scorecard

| Evaluation Area | Result | Status |
|---|---|---|
| Evaluation dataset verification | 60 questions | PASS |
| Local FAQ retrieval | 73.17% source-match rate | MEASURED |
| Automated regression suite | 408 passed, 0 failed, 4 skipped | PASS WITH BLOCKED USE CASES |
| Authentication checks | 4/4 passed | PASS |
| Synthetic two-user isolation | 1 passed | PASS - SERVICE LEVEL ONLY |
| Local FAQ retrieval latency | p95 21.07 ms | MEASURED |
| Chatbot response-quality scoring | Not completed | PENDING |
| Real financial backend | Not connected | BLOCKED |
| Production cross-user isolation | Not verified | BLOCKED |
| Production secret configuration | Placeholder detected | BLOCKED |
| Production release clearance | Not granted | BLOCKED |

## 10. Final Assessment

The local Department 3 implementation passed 408 automated tests with zero failures. Four tests remain skipped because the required financial-data retrieval capabilities are unavailable.

All four previously executed direct authentication checks passed. The new synthetic two-user service-level isolation test also passed.

The verified-source retrieval benchmark achieved a 73.17% expected-source match rate. Local FAQ retrieval latency was measured at a p95 of 21.07 ms.

However, actual chatbot response scoring, real financial backend integration, production authentication configuration, and production cross-user isolation verification remain outstanding.

**Final Decision: PARTIALLY COMPLETE - NOT CLEARED FOR PRODUCTION RELEASE.**
