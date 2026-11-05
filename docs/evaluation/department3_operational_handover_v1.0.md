# Department 3 - Operational Handover Document

**Project:** HisabDo Expense Management Chatbot  
**Department:** Department 3  
**Document Version:** 1.1  
**Handover Date:** 5 November 2026  
**Release Status:** NOT CLEARED FOR PRODUCTION

## 1. Purpose

This document provides operational guidance for monitoring, maintaining, testing, and troubleshooting the Department 3 financial assistant.

It records the current implementation, available test evidence, known limitations, and activities required before production deployment.

## 2. Current System Status

| Area | Current Status |
|---|---|
| Automated regression suite | 408 passed, 4 skipped, 0 failed |
| Full-suite warnings | 2 |
| FAQ evaluation dataset | 60 questions |
| Verified-source retrieval match | 30 of 41 (73.17%) |
| Retrieval outcome distribution | 30 MATCH, 11 MISS, 13 SAFE_ABSTENTION, 6 REVIEW |
| Local FAQ retrieval latency | Average 18.47 ms; p95 21.07 ms |
| Direct authentication checks | 4 of 4 passed |
| Synthetic user isolation test | 1 passed |
| Real financial backend | Not integrated |
| Production cross-user isolation | Not verified |
| Production secret | Development placeholder detected |
| Production release | Blocked |

The 73.17% result represents verified-source retrieval matching, not end-to-end chatbot answer accuracy.

## 3. Operational Monitoring

The Department 3 monitoring implementation records operational events and counters.

Monitor the following areas:

- Request success and failure counts.
- Provider failures.
- Retrieval success and empty retrieval events.
- Response latency.
- Error categories.
- Model/provider usage where available.

**Important limitations:**

- Monitoring counters are currently in memory.
- Counters reset when the application restarts.
- A persistent metrics exporter is not configured.
- Live production API cost measurement is not available.
- Local retrieval latency is not equivalent to complete chatbot response latency.

## 4. Privacy and Logging Rules

Operational logs must contain only approved, non-sensitive information.

Allowed:

- Event name.
- Component name.
- Outcome.
- Latency.
- Error category.
- Provider/model metadata.
- Retrieved source IDs.

Never log:

- Passwords or authentication tokens.
- Customer names and private identifiers.
- Account balances or transaction records.
- Raw financial payloads.
- Raw user messages or chatbot responses.
- API keys or confidential credentials.

Review logging configuration before any production deployment.

## 5. Backend and Authentication Operations

The current backend client is a `MockBackendClient`.

When financial data is requested, it returns a safe backend-unavailable error rather than inventing account information.

Current expected behavior:

- Missing internal token: reject request.
- Invalid internal token: reject request.
- Missing authenticated user ID: reject request.
- Mismatched request and authenticated user IDs: reject request.
- Unavailable financial backend: return safe HTTP 503 response.

Direct local authentication verification recorded:

- Missing token: HTTP 401.
- Wrong token: HTTP 401.
- Missing user ID: HTTP 401.
- Valid configured credentials: HTTP 200.

**Production requirement:** Integrate the real authenticated backend and ensure user identity is derived from a trusted login/session. Do not use test-only identity headers in production.

The configured internal token remains a development placeholder and must not be used as a production secret.

## 6. Synthetic User Isolation Evidence

The test file:

`tests/test_department3_user_isolation.py`

was executed with:

`python -m pytest tests\test_department3_user_isolation.py -v`

Recorded result:

- 1 passed.
- Two synthetic users were tested.
- Backend request identities were checked.
- Unique synthetic financial markers were checked for separation.
- The test used a fake backend and provider at the service layer.

This is local synthetic test evidence only. It does not prove production tenant isolation or zero data leakage against a real authenticated financial backend.

## 7. FAQ Knowledge Base Maintenance

The FAQ knowledge base is maintained in:

`data/faq_docs.json`

Current evaluation dataset:

`docs/evaluation/department3_evaluation_set_v1.0.csv`

Retrieval results:

`docs/evaluation/retrieval_results_v1.0.csv`

Maintenance procedure:

1. Review the official source before adding or changing an FAQ.
2. Confirm the information is accurate and relevant to HisabDo.
3. Record source metadata and review status.
4. Mark unsupported information as needing review.
5. Validate the updated JSON structure.
6. Run FAQ retrieval and security tests.
7. Review retrieval results before accepting the update.
8. Preserve a backup of the existing knowledge base.

Do not convert unverified information into verified content.

## 8. Testing and Benchmark Commands

Run commands from the repository root.

**Full automated regression suite**

```powershell
python -m pytest -q -rs
```

**Focused financial API and FAQ security tests**

```powershell
python -m pytest tests\test_financial_api_security.py tests\test_faq_rag_security.py -v
```

**Synthetic user isolation test**

```powershell
python -m pytest tests\test_department3_user_isolation.py -v
```

**Local retrieval latency benchmark**

```powershell
python docs\evaluation\department3_latency_benchmark.py
```

**Review current repository changes**

```powershell
git status --short
```

**Check whitespace and patch errors**

```powershell
git diff --check
```

Review all test failures, warnings, skipped cases, and generated outputs before accepting a release candidate.

## 9. Known Limitations and Pending Work

The following issues remain open:

1. Real authenticated financial backend integration is pending.
2. Production secret configuration is pending.
3. Actual cross-user data isolation testing is pending.
4. Four Day 17 use-case tests remain skipped because the required grounded financial data layer is unavailable:
   - Transaction-level answers.
   - Budget answers.
   - Multi-period comparisons.
   - Trend and insight answers.
5. Eleven retrieval evaluation cases are marked as misses.
6. Six retrieval cases require manual review.
7. Final chatbot response quality scoring has not been completed.
8. Production monitoring persistence and live provider cost measurement are not configured.

The 73.17% result represents verified-source retrieval matching, not end-to-end chatbot answer accuracy.

## 10. Incident Handling

If an operational or security issue occurs:

1. Record the time, affected component, and sanitized error category.
2. Avoid copying customer financial data or credentials into incident notes.
3. Check application and backend availability.
4. Review authentication and authorization failures.
5. Run the relevant regression and security tests.
6. Escalate backend, authentication, or data-isolation issues to the authorized backend/security owner.
7. Keep production release blocked if financial data protection cannot be confirmed.
8. Record the corrective action and verification evidence.

## 11. Production Readiness Checklist

- [ ] Production secret securely configured.
- [ ] Real authenticated backend integrated.
- [ ] Trusted login/session identity verified.
- [ ] User-specific backend authorization verified.
- [ ] Two-user isolation tests passed against the real backend.
- [ ] No cross-user financial data leakage observed.
- [ ] Skipped financial use cases implemented and tested.
- [ ] Evaluation dataset manually reviewed.
- [ ] Final chatbot responses scored using the evaluation rubric.
- [ ] Production monitoring and alerting configured.
- [ ] Privacy-safe logging reviewed.
- [ ] Regression and security suites passed.
- [ ] Authorized technical/security approval obtained.

## 12. Handover Responsibilities

| Responsible Role | Handover Responsibility |
|---|---|
| Backend Owner | Real backend integration and user-level authorization |
| Security Owner | Production secrets, authentication, and isolation approval |
| AI/ML Owner | Retrieval quality, response evaluation, and safety checks |
| Operations Owner | Monitoring, incident handling, and deployment readiness |
| Project Owner | Final release decision and acceptance |

Role assignments must be confirmed by the project team. No individual ownership is assumed in this document.

## 13. Final Handover Decision

The local Department 3 evaluation work has produced a final evaluation scorecard, baseline comparison report, security release clearance checklist, and operational handover documentation.

The latest recorded automated regression suite passed 408 tests, with four documented skips, zero failures, and two warnings.

Direct local authentication checks passed 4 of 4 cases. The synthetic service-layer user isolation test passed, but it does not establish production isolation.

Real financial backend integration, production authentication configuration, production cross-user isolation, final chatbot response scoring, and production monitoring remain unverified.

**Final Status: HANDOVER DOCUMENTATION PREPARED - PRODUCTION RELEASE BLOCKED.**

Production approval must only be granted after all security, backend, evaluation, and operational blockers are resolved and verified.
