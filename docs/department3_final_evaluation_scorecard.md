# Department 3 Final Evaluation Scorecard

Evaluation date: 2026-11-04
Dataset version: 1.0.0
Release candidate: Final evaluation review
Overall release status: NOT CLEARED

## 1. Evaluation Summary

The local test suites passed. Retrieval quality results are available.
However, production financial backend verification and complete answer quality evaluation remain pending.

## 2. Test Results

| Test suite | Result | Status |
|---|---|---|
| Full project suite | 325 passed, 4 skipped | PASS |
| Security tests | 23 passed | PASS |
| Chatbot tests | 11 passed | PASS |
| Retrieval tests | 2 passed | PASS |
| Safety guardrails | 6 passed | PASS |

One dependency deprecation warning was reported in targeted test runs. No test failures were reported in these runs.

These are separate test executions and their counts must not be added as unique tests.

## 3. Retrieval Evaluation

Dataset: data/department3_evaluation_v1.json

Results: docs/department3_evaluation_v1_results.json

| Metric | Result |
|---|---:|
| Evaluation questions | 71 |
| Answerable cases | 55 |
| No answer or clarification cases | 16 |
| Hit at 1 | 89.09% |
| Hit at 3 | 96.36% |
| No answer cases with retrieved sources | 16 of 16 |

All 16 no answer or clarification cases retrieved a source. Retrieval results alone cannot confirm that the assistant correctly refuses or asks for clarification.

## 4. Historical Baseline

| Retrieval method | Hit at 1 | Hit at 3 |
|---|---:|---:|
| Historical TF IDF | 68.75% | 93.75% |
| Normalized query | 68.75% | 93.75% |
| Synonym expansion | 81.25% | 93.75% |
| Expansion with reranking | 81.25% | 87.50% |
| Department 3 evaluation | 89.09% | 96.36% |

The historical and Department 3 datasets differ. This table is informational and does not establish a controlled before and after improvement.

## 5. Release Quality Criteria

| Criterion | Evidence | Status |
|---|---|---|
| Local regression tests | 325 passed, 4 skipped | PASS |
| Chatbot routing | 11 tests passed | PASS |
| Retrieval behavior | 2 tests passed | PASS |
| Security guardrails | 6 tests passed | PASS |
| Cross user boundary tests | 23 security tests passed | PASS |
| Generated answer factual accuracy | No response level scoring available | PENDING |
| Citation correctness | Not evaluated | PENDING |
| Answer completeness | Not evaluated | PENDING |
| Language quality | Not evaluated | PENDING |
| Safe abstention on all evaluation cases | Not evaluated end to end | PENDING |
| Production latency percentiles | No production measurements | PENDING |
| Production provider cost | No verified usage data | PENDING |
| Real backend financial data verification | Real backend contract unavailable | BLOCKED |
| Production session isolation | Not verified under production conditions | BLOCKED |
| Source approval and privacy clearance | Audit remains partial | PENDING |

## 6. Backend and Security Findings

The inspected backend client contains a mock implementation with sample financial values. Production mode disables mock financial data and returns HTTP 503 when the real backend is not configured.

The service code routes the user's own financial questions through the backend client rather than RAG. Security tests verify identity checks and cross user request protections.

These findings do not prove that real production account balances and expenses were retrieved or isolated correctly.

## 7. Data and Evaluation Limitations

The baseline report lists 12 knowledge documents. The inspected source inventory contains 12 FAQ records and 6 sample financial knowledge records. The document count requires reconciliation.

The current retrieval evaluation does not score generated answers, citations, completeness, language quality, or safety.

## 8. Final Decision

LOCAL TEST VALIDATION: PASS

RETRIEVAL EVALUATION: MEASURED

PRODUCTION FINANCIAL DATA VERIFICATION: BLOCKED

END TO END ANSWER QUALITY: PENDING

PRODUCTION SECURITY CLEARANCE: NOT GRANTED

RELEASE DECISION: NOT CLEARED

Production release must remain on hold until the real backend contract is configured, production data isolation is verified, and complete answer quality and latency evaluation evidence is available.

Latest full suite rerun: 325 passed, 4 skipped, 0 failed, 1 warning, completed in 8.39 seconds on 2026-11-04.
