# Day 7 — Department 3 Final Evaluation & Operational Handover

Date: 4 November 2026
Project: HisabDo AI Business Assistant
Department: Department 3
Branch: purnoor-zafar-ai-intern

## 1. Final Evaluation Scorecard

| Evaluation | Result | Status |
|---|---|---|
| Full pytest suite | 353 passed, 4 skipped | PASS |
| Targeted security tests | 38 passed | PASS |
| Cross-user boundary tests | 19 passed | PASS |
| Chatbot tests | 16 passed | PASS |
| Backend client tests | 3 passed | PASS |
| Integration API tests | 3 passed | PASS |
| FAQ retrieval | 10/10 passed | PASS |
| Production financial API | Not verified | BLOCKED |
| Production session isolation | Not verified | BLOCKED |
| Latency and API costs | Not measured | PENDING |

## 2. Baseline vs Final Model Comparison

Dataset: data/expense_data.csv
Training rows: 397
Test rows: 103
Description overlap: 0

| Metric | Baseline | Fresh evaluation | Saved model |
|---|---:|---:|---:|
| Accuracy | 78.64% | 78.64% | 78.64% |
| Weighted precision | 85.92% | 85.92% | 85.92% |
| Weighted recall | 78.64% | 78.64% | 78.64% |
| Weighted F1 | 79.03% | 79.03% | 79.03% |

Conclusion: Saved model matches the historical benchmark. No measurable improvement or regression was observed.

Weak categories:
- Groceries: F1 0.50, support 2
- Bills: F1 0.62, support 13
- Utilities: F1 0.67, support 5
- Entertainment: F1 0.71, support 20

## 3. Security Release Clearance Checklist

| Check | Local result | Production status |
|---|---|---|
| Missing/invalid internal token | 401 tests passed | Not independently verified |
| Missing user identity | 401 test passed | Trusted identity not verified |
| Mismatched user identity | 403 test passed | Real session isolation not verified |
| Third-party financial query blocking | Tests passed | Production verification pending |
| Own financial query backend path | Local tests passed | Real backend not connected |
| Mock financial data labelled | 3 tests passed | Demo data only |
| All financial routes protected | Not fully established | Blocked |
| Two-user production isolation | Not tested | Blocked |

Production security clearance is NOT GRANTED. The current MockBackendClient returns demonstration figures, not real customer financial data. Trusted upstream identity and actual backend integration remain unverified.

## 4. Operational Handover

Important components:
- src/financial_assistant/router.py
- src/financial_assistant/service.py
- src/security.py
- src/integration/backend_client.py
- src/expense_categorization/train_model.py
- src/expense_categorization/prediction_service.py

Reproducible checks:
- python -m pytest -q
- python tests/run_evaluation.py
- python -m pytest tests/test_chatbot.py tests/test_cross_user_data_boundary.py tests/test_backend_client.py -q
- python -m pytest tests/test_integration_api.py -v

Before production release:
1. Connect and verify the real financial backend.
2. Verify trusted authentication middleware and identity propagation.
3. Protect all relevant financial routes.
4. Test two independent authenticated users against backend test accounts.
5. Measure response latency and provider/API costs.
6. Re-run tests and obtain authorized release approval.

Operational limitations:
- Never expose API keys or internal tokens in logs.
- Never treat mock figures as customer data.
- Investigate 4 skipped tests and 4 warnings before sign-off.
- Preserve existing untracked backup files.

## 5. Final Release Decision

Local evaluation: PASSED for the checks listed above.
Model comparison: PASSED — saved model matches baseline.
Production integration and security: BLOCKED / NOT VERIFIED.
Latency and cost: NOT MEASURED.

Recommendation: Keep the release candidate pending until real backend integration, trusted authentication, production-like isolation tests, latency/cost measurements and authorized sign-off are complete.

Prepared for: XICTEK Systems — AI/ML Internship

## 6. Final Repeat Verification — 4 November 2026

A final repeat verification was performed after preparing the handover report.

| Check | Latest result |
|---|---|
| Full pytest suite | 353 passed, 4 skipped |
| Total runtime | 6.79 seconds |
| FAQ retrieval questions | 10 |
| Retrieval checks passed | 10/10 |
| Needs review | 0 |
| Warnings | 4 |

All 10 FAQ retrieval checks passed, including the ambiguous balance query and unsupported integration query, which correctly returned no match.

The repeat verification confirms the previously recorded local results. It does not establish production backend availability, real-user session isolation, or production release clearance.
