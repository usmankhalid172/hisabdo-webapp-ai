# Known Limitations and Risk Register

## Purpose
This register documents limitations and risks that must be considered before production deployment. Items marked pending require verification rather than being treated as confirmed defects.

| Risk / limitation | Impact | Status / action |
|---|---|---|
| Upstream application authentication integration | User identity is trustworthy only when the application backend validates its login/session and supplies the identity to the AI service through a trusted request. | Integration not confirmed. Verify the upstream authentication contract and end-to-end behaviour. |
| Internal service token configuration | Missing or incorrect service-token configuration should cause protected requests to be rejected. Incorrect deployment configuration can make integration fail. | Verify secure configuration in each environment. |
| Live LLM provider behaviour | Automated tests may not prove that external provider credentials, network access, rate limits, and live responses work in production. | Verify using an approved test environment and valid secret configuration. |
| Knowledge-base coverage | Missing, outdated, or contradictory FAQ entries may result in incomplete or fallback answers. | Review `data/faq_docs.json` regularly and test representative questions. |
| Retrieval quality | Relevant information may not always be retrieved for ambiguous or differently phrased questions. | Evaluate retrieval against a maintained question set and review weak results. |
| Financial data source | Synthetic/sample data or mocked backends are not evidence that live customer transactions are connected correctly. | Confirm the real backend contract, data ownership, and response validation before launch. |
| Cross-user data isolation | A regression in identity checks or data scoping could expose another user's information. | Keep authorization tests in CI and verify isolation through the real integration. |
| Multilingual responses | Coverage of selected English/Urdu/Roman Urdu examples does not guarantee reliable handling of every phrasing. | Expand representative test cases and manually review failures. |
| Skipped tests and warnings | Skips may leave behaviour untested; warnings may indicate deprecated or risky patterns. | Inspect the full test output and document the cause of each item. |
| Production operational readiness | Automated tests alone do not establish monitoring, logging, rate limiting, secret rotation, backups, or deployment rollback readiness. | Complete an environment-specific production checklist. |

## Security Requirements
- Never commit API keys, internal tokens, passwords, or real customer financial data.
- Store secrets in the approved environment or secret manager.
- Use HTTPS and restrict internal service access.
- Ensure the upstream application validates user sessions before forwarding identity.
- Return only data authorized for the authenticated user.
- Avoid logging tokens or sensitive financial details.
- Review dependency and configuration risks before production release.

## Release Gate
Production approval should wait until high-priority integration and security checks have been verified, skipped tests and warnings reviewed, and the responsible reviewer has recorded a decision.

## Sign-off
- Team lead review: Pending confirmation.
- QA sign-off: Pending confirmation.
- Production deployment approval: Pending confirmation.
