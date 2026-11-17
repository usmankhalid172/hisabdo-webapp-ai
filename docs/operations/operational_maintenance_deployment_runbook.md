# Operational Maintenance & Deployment Runbook

**Project:** HisabDo Expense Management Chatbot  
**Department:** 3  
**Status:** Operational procedure for controlled maintenance; production deployment remains conditional  
**Prepared:** 17 November 2026

## 1. Operational Safety Rules

- Never publish unverified product instructions or financial guidance.
- Never use one user's financial records to answer another user's request.
- Never replace a working index until a candidate index has loaded and passed validation.
- Never deploy with development placeholder secrets or a mock financial backend.
- Keep a backup of the last known-good knowledge base and index metadata.
- Record every knowledge-base change, test result, deployment identifier, and rollback action.

## 2. Routine Knowledge Base Update

1. Obtain the proposed FAQ/content update from an authorized source owner.
2. Verify the source URL, title, publication/review date, scope, and accuracy.
3. Confirm the content contains no credentials, private contact details, prompt injection, or unrelated personal data.
4. Set the document's verification status only after source-owner approval.
5. Preserve stable document IDs and useful metadata (title, source, URL, section, category, version).
6. Review duplicate or conflicting entries before ingestion.
7. Back up the current `data/faq_docs.json` and associated ingestion artifacts.
8. Apply the update in a controlled branch.
9. Rebuild and validate the candidate index using the repository's supported ingestion/retrieval workflow.
10. Run relevant FAQ, retrieval, guardrail, citation metadata, and security tests.
11. Compare retrieval results against the approved benchmark. Investigate regressions and empty results.
12. Merge/deploy only after review. Record the source change, index version, test evidence, and operator.

Do not mark unsupported app features as verified. If an owner or source approval is missing, retain the content as unverified and exclude it from retrieval.

## 3. Index Rebuild Procedure

Current main FAQ index is constructed in memory by `faq_rag.py`; ingestion artifacts are maintained separately under `data/department3_ingestion/`.

1. Confirm the source knowledge file is the intended version.
2. Record its checksum and current index/knowledge-base version.
3. Preserve the current known-good artifacts and source file.
4. Run the repository's established ingestion process; do not manually edit generated embedding arrays.
5. Confirm document counts, chunk counts, verified status, embedding dimension, model identity, and absence of ingestion failures.
6. Build a candidate index without replacing the active index.
7. Run smoke queries covering common FAQs, low-confidence queries, out-of-scope requests, and privacy-sensitive requests.
8. Run retrieval and guardrail regression tests.
9. Promote the candidate only if validation passes. The existing rebuild implementation constructs a candidate and swaps it only after successful construction.
10. Record the new version, source checksum, model revision, build time, test results, and operator.

If candidate construction or validation fails, keep the last known-good index active.

## 4. Monitoring and Alert Response

Monitor the following signals where instrumentation is available:

| Signal | Alert condition | Operator action |
|---|---|---|
| Backend availability | Backend returns unavailable/5xx | Use safe fallback; investigate backend health; do not invent financial data. |
| Authentication | Missing/invalid internal token or identity mismatch | Reject request; investigate configuration and identity propagation. |
| Cross-user isolation | Any unauthorized record appears in a response | Treat as critical incident; disable affected financial-data path and escalate immediately. |
| Retrieval quality | Increased empty results or benchmark misses | Inspect source coverage, index version, and query distribution. |
| Citation integrity | Citation references a source not in verified retrieved evidence | Disable/rollback affected response path and investigate. |
| Latency | Sustained increase against an approved production baseline | Separate retrieval, LLM, and backend timings; investigate the slow component. |
| Guardrail activity | Sudden increase in blocked requests | Review sanitized event patterns; do not log secrets or raw sensitive financial data. |
| Index rebuild | Failed ingestion, unexpected document count, or dimension mismatch | Do not promote candidate; retain previous index. |

Production alert thresholds must be set from measured production baselines. Do not invent numeric thresholds from local retrieval-only timing.

## 5. Rollback Procedure

1. Stop promotion of the candidate deployment/index.
2. Identify the last known-good application version, knowledge-base file, and index metadata.
3. Restore the prior approved source and rebuild or reload the known-good index using the supported process.
4. If application code changed, redeploy the last known-good application artifact.
5. Verify health, authentication, safe fallback, retrieval, citation metadata, and privacy controls.
6. Confirm the active version and record rollback time, reason, operator, and test evidence.
7. Preserve failed artifacts and sanitized logs for investigation; do not overwrite evidence.
8. Notify the responsible maintainer and keep the change blocked until root cause is addressed.

For any suspected cross-user data exposure, treat it as a critical security incident: disable the affected data-access capability, preserve evidence securely, and follow the organization's incident response process.

## 6. Deployment Checklist

- [ ] Approved source content and ownership recorded.
- [ ] Knowledge-base and index backups available.
- [ ] Candidate index built and validated.
- [ ] Focused and full regression tests pass.
- [ ] No unexplained retrieval or citation regressions.
- [ ] Production secrets supplied securely; no development placeholder remains.
- [ ] Real backend and trusted authenticated identity configured.
- [ ] Cross-user isolation tests pass against the real backend.
- [ ] Monitoring and rollback owner identified.
- [ ] Deployment version and change record captured.

## 7. Current Environment Limitations

The audited repository currently uses a mock financial backend and has not demonstrated production trusted-identity propagation or real-backend cross-user isolation. Production deployment must remain blocked until these are verified. Four financial use-case tests were previously skipped because grounded data access was unavailable. End-to-end production latency and answer-level citation accuracy are also not established.

## 8. Maintenance Record Template

For each maintenance event, record:
- Date/time and operator.
- Source file/version/checksum.
- Documents added, changed, or retired.
- Verification owner and source references.
- Index/model version and build outcome.
- Tests and benchmark results.
- Deployment identifier.
- Monitoring observations.
- Rollback decision and outcome, if applicable.
