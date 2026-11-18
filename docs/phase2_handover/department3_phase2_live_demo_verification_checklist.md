# Department 3 — Phase 2 Live Demo Verification Checklist

**Project:** HisabDo Expense Management Chatbot  
**Department:** Department 3  
**Status:** Prepared — Live execution pending  
**Date:** 18 November 2026

## 1. Demonstration Details

| Field | Record |
|---|---|
| Demonstration date/time | Pending |
| Environment / URL | Pending |
| Application version / commit | Pending |
| Presenter | Pending |
| Stakeholder / reviewer | Pending |
| Test account | Authorized test account required |
| Backend type | Production backend not yet verified |
| Evidence location | Pending |

## 2. Live Demonstration Checklist

For every test, record the actual observed response, screenshot/log reference, pass/fail result, and reviewer comments.

| # | Demonstration scenario | Expected verification | Status |
|---|---|---|---|
| 1 | Verified FAQ retrieval | Relevant verified source is retrieved | Pending |
| 2 | Retrieval accuracy | Results compared against approved evaluation questions | Pending |
| 3 | Grounded answer | Answer stays within retrieved evidence | Pending |
| 4 | Inline citations | Citations identify the supporting source accurately | Pending |
| 5 | Unsupported question | Assistant abstains or safely clarifies | Pending |
| 6 | Multi-turn financial conversation | Context is maintained without inventing financial data | Pending |
| 7 | Transaction flow | No transaction is saved without verified backend authorization and user confirmation | Pending |
| 8 | Budget and expense queries | Correct data-backed response or safe unavailable response | Pending |
| 9 | Authentication | Missing or invalid credentials are rejected | Pending |
| 10 | User isolation | One user's financial information cannot be accessed by another user | Pending |
| 11 | Prompt injection | Unsafe instructions are rejected or safely handled | Pending |
| 12 | Sensitive output | Private or unauthorized financial information is not disclosed | Pending |
| 13 | Backend failure | Safe fallback is returned without fabricated figures | Pending |
| 14 | Monitoring and latency | Actual response timings and operational events are recorded | Pending |

## 3. Day 1 vs Day 9 Evidence Comparison

Use the same dataset, evaluation questions, scoring rules, and test environment wherever possible.

| Metric | Day 1 evidence | Day 9 evidence | Verification |
|---|---|---|---|
| Retrieval source-match rate | 30/41 (73.17%) | Not yet verified | Pending |
| Verified-source retrieval match rate | Day 1 audit: 73.17% source-match rate; Day 9 comparable result not verified | Comparable Day 9 result pending | Pending |
| Grounded answer accuracy | Not established | Not established | Pending |
| Inline citation accuracy | Not established | Not established | Pending |
| Multi-turn flow success | Not independently established | Not independently established | Pending |
| Safety guardrail tests | Historical evidence requires baseline mapping | Later test evidence requires mapping | Pending |
| Full automated test suite | 408 passed, 4 skipped (earlier record) | 456 passed, 4 skipped (later record) | Different recorded runs; not a direct improvement comparison |

**Important:** The historical retrieval figures above are not necessarily Day 1 and Day 9 measurements. Confirm dates and matching evaluation methodology before treating them as a day-to-day comparison.

## 4. Required Evidence to Capture

- [ ] Screenshot or recording of the live application.
- [ ] Test questions and actual chatbot responses.
- [ ] Retrieved source IDs and inline citations.
- [ ] Multi-turn conversation transcript.
- [ ] Safety and prompt-injection test results.
- [ ] Authentication and cross-user isolation evidence.
- [ ] Backend health and error logs.
- [ ] Actual latency measurements.
- [ ] Day 1 and Day 9 benchmark result files.
- [ ] Stakeholder feedback and acceptance decision.

Do not include real customer financial information, passwords, API keys, or private account identifiers in screenshots or reports. Use authorized synthetic test accounts and data.

## 5. Demonstration Outcome

**Overall result:** Pending live execution.

**Passed scenarios:** Not yet recorded.  
**Failed scenarios:** Not yet recorded.  
**Blocked scenarios:** Not yet recorded.  
**Evidence reviewed by:** Pending.  
**Stakeholder comments:** Pending.

## 6. Release Decision

Production clearance must remain blocked until the real backend, trusted identity, cross-user isolation, skipped financial use cases, citation quality, and operational readiness are independently verified.

**Current disposition: NOT PRODUCTION CLEARED.**

---
**Document owner:** Department 3  
**Document status:** Ready for live walkthrough and evidence capture



## Focused Local Test Evidence — 19 November 2026

Focused verification across 11 test files: 142 passed, 4 skipped, 0 failed, 2 deprecation warnings; runtime 33.14 seconds.

Verified locally: chatbot behavior, FAQ retrieval and security, guardrails, API authentication, multilingual handling, ingestion, monitoring, and synthetic/user-isolation test coverage.

Conversational history and FAQ follow-up tests are covered locally. Full data-backed multi-turn financial workflows remain unverified.

Skipped: transaction lookup, budget, multi-period comparison, and trends/aggregates because the required financial data retrieval layer is unavailable.

This is local automated test evidence, not a live production demonstration. Production demo and stakeholder walkthrough remain pending.
