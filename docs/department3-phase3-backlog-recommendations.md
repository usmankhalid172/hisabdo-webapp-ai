# Department 3 — Open Backlog and Phase 3 Recommendations

**Date:** 18 November 2026

| ID | Priority | Open item | Recommended next action | Acceptance evidence |
|---|---|---|---|---|
| P3-01 | P1 | Production financial backend and session isolation not verified | Integrate the approved real backend and validate authenticated account scoping | Authorized integration tests and stakeholder security approval |
| P3-02 | P1 | Full multi-turn financial workflows not independently verified | Test expense/income entry, missing-field follow-up, correction, confirmation, and report flow end to end | Repeatable workflow test evidence |
| P3-03 | P1 | Production deployment and operational sign-off pending | Perform controlled staging/production readiness review | Deployment record and authorized sign-off |
| P3-04 | P2 | Inline citation rendering and source-conflict handling not verified in financial chatbot UI | Validate source IDs/URLs through API response and actual UI rendering | UI/API evidence for valid, missing, and conflicting sources |
| P3-05 | P2 | End-to-end latency and provider cost not measured | Add timing and usage instrumentation across retrieval, LLM, and backend | Reproducible latency/cost report |
| P3-06 | P2 | EVAL-08 expected finance_001 missing from top 3; Precision@3 0.4583 | Improve query coverage, ranking, and evaluation dataset | Updated benchmark with regression protection |
| P3-07 | P2 | scikit-learn artifact/runtime version mismatch (artifact 1.7.2; runtime 1.5.2) | Align training and serving versions or regenerate compatible artifact | Clean model load and prediction test |
| P3-08 | P3 | pytest-asyncio loop-scope warning | Set explicit asyncio fixture loop scope | Warning removed in test run |
| P3-09 | P3 | Starlette/AnyIO deprecation warning | Upgrade compatible dependencies and rerun regression suite | Deprecation warning resolved |

## Phase 3 delivery order
1. Production backend, authentication, and tenant/session isolation.
2. Full financial workflow integration tests.
3. Citation rendering and source conflict verification.
4. End-to-end observability, latency, and provider-cost measurement.
5. Retrieval benchmark improvements and dependency/model compatibility.
6. Production deployment review, rollback rehearsal, and stakeholder acceptance.

No item above should be marked closed without its stated acceptance evidence.
