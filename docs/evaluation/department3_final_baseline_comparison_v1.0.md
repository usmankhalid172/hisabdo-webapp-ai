# Department 3 - Final Baseline Comparison Report

**Project:** HisabDo Expense Management Chatbot  
**Department:** Department 3 - Expense Management  
**Report Version:** 1.1  
**Evaluation Date:** 5 November 2026  
**Status:** Local Evaluation Updated - Production Validation Pending

## 1. Purpose

This report compares the historical Department 3 evaluation with the latest available local test, retrieval, authentication, latency, and synthetic isolation evidence.

The comparison distinguishes measured results from capabilities that remain unverified.

## 2. Historical Baseline

The earlier exploratory evaluation covered 19 questions.

| Baseline Outcome | Questions |
|---|---:|
| Clear passes | 11 |
| Retrieval issues | 6 |
| Partial response | 1 |
| Backend limitation | 1 |
| **Total** | **19** |

These results were exploratory and were not a complete response-quality benchmark.

## 3. Retrieval Evaluation

The current evaluation dataset contains 60 questions.

| Metric | Current Measurement |
|---|---:|
| Total evaluation questions | 60 |
| Verified-source questions | 41 |
| Unverified questions | 17 |
| Questions without a verified source | 2 |
| Expected-source matches | 30 |
| Expected-source misses | 11 |
| Source-match rate | 73.17% |

**Measured improvement: No overall improvement established.**

The source-match rate is calculated as 30 matches out of 41 verified-source questions. It is a retrieval source-match measurement, not chatbot answer accuracy.

The historical 19-question exploratory evaluation and the current 60-question retrieval evaluation have different scopes. They should not be treated as directly comparable accuracy benchmarks.

## 4. Retrieval Outcome Distribution

| Outcome | Questions |
|---|---:|
| MATCH | 30 |
| MISS | 11 |
| SAFE_ABSTENTION | 13 |
| REVIEW | 6 |
| **Total** | **60** |

The 13 safe-abstention outcomes represent retrieval-level no-document results. They do not independently prove generated chatbot response quality.

The six review cases require manual relevance and source-suitability assessment.

## 5. Automated Test Comparison

| Test Evidence | Historical Result | Latest Result |
|---|---:|---:|
| Earlier broad test suite | 351 passed, 4 skipped | 408 passed, 4 skipped |
| Failed tests | Historical failure count not used for comparison | 0 |
| Warnings | Historical warning details not used for comparison | 2 |

The latest full test run completed with **408 passed, 4 skipped, 0 failed, and 2 warnings in 52.73 seconds**.

The four skipped tests require transaction-level, budget, historical comparison, and trend/aggregate data capabilities.

The latest local suite passing does not establish that unavailable backend-dependent features are operational.

## 6. Authentication Comparison

Direct authentication checks used the actual authentication dependency rather than a test fixture override.

| Case | Expected Status | Observed Status |
|---|---:|---:|
| Missing token | 401 | 401 |
| Wrong token | 401 | 401 |
| Missing authenticated user ID | 401 | 401 |
| Valid configured credentials | 200 | 200 |

All four local checks passed.

The configured internal token remains a development placeholder. Production-grade secret configuration and verification are still required.

## 7. Synthetic User Isolation Test

The test `tests/test_department3_user_isolation.py` completed successfully.

| Evidence | Result |
|---|---|
| Test result | 1 passed |
| Synthetic users | customer-a and customer-b |
| Backend request identity | Checked for both users |
| Unique financial markers | Checked for separation between contexts |
| Response source | backend_financial_api |

This test provides service-layer evidence using a synthetic fake backend and provider.

It does not demonstrate isolation against a real authenticated financial backend, real user accounts, production sessions, or production infrastructure.

## 8. Latency Comparison

The available local FAQ retrieval benchmark reports:

| Metric | Current Measurement |
|---|---:|
| Average | 18.47 ms |
| p50 | 18.47 ms |
| p95 | 21.07 ms |
| Maximum | 21.37 ms |

These values represent local FAQ retrieval measurements only.

No comparable end-to-end chatbot baseline, external provider latency benchmark, or production-like load test is available.

## 9. Financial Backend and Data Isolation

The current backend client is a safe unavailable-backend implementation.

It returns HTTP 503 when actual account-specific financial data is requested.

This prevents fabricated financial figures, but does not demonstrate successful retrieval from a real authenticated financial backend.

The service-layer synthetic isolation test passed. However, real cross-user financial data isolation remains unverified.

## 10. Improvement Summary

| Area | Latest Evidence | Conclusion |
|---|---|---|
| Payable/receivable targeted retrieval | Four targeted queries retrieved relevant guidance | Specific retrieval improvement demonstrated |
| Complete retrieval evaluation | 30/41 expected sources matched | Overall improvement not established |
| Automated regression | 408 passed, 0 failed | Latest local suite passed |
| Authentication | 4/4 direct checks passed | Local authentication checks passed |
| Synthetic user isolation | 1 test passed | Synthetic service-layer isolation demonstrated |
| Financial backend | Safe HTTP 503 fallback remains | Real backend integration unavailable |
| Production isolation | Not tested with real accounts | Unverified |
| Response quality | Actual responses not scored across all 60 questions | Pending |
| FAQ retrieval latency | p95 21.07 ms | Local retrieval benchmark only |

## 11. Outstanding Work

The following activities remain necessary:

1. Connect the approved authenticated financial backend.
2. Replace the development placeholder with a production-grade internal service secret.
3. Verify that authenticated identity is derived from a trusted application login/session.
4. Run cross-user isolation tests with authorized test accounts and synthetic financial data.
5. Execute all 60 questions through the authorized chatbot environment.
6. Score actual responses using the seven-dimension evaluation rubric.
7. Review the 11 retrieval misses and six manual-review cases.
8. Conduct production-like load and end-to-end latency testing.

## 12. Conclusion

The latest local evaluation demonstrates a passing automated regression suite, successful direct local authentication checks, and a passing synthetic service-layer user isolation test.

The recorded retrieval source-match rate is 73.17%. No overall retrieval improvement or final chatbot answer-accuracy percentage has been established.

Real financial backend integration, production secret configuration, production cross-user isolation, and full response-quality evaluation remain pending.

**Final Comparison Decision: LOCAL TESTING PASSED; FULL PERFORMANCE VALIDATION AND PRODUCTION SECURITY CLEARANCE REMAIN PENDING.**
