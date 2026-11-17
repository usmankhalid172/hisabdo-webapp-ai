# Department 3 — Operational Maintenance and Deployment Runbook

## 1. Purpose
This runbook describes the recommended operational checks, maintenance activities, and deployment verification process for the HisabDo Department 3 AI assistant.

## 2. Pre-Deployment Checklist
- Confirm the intended Git branch and reviewed commit.
- Confirm required environment variables are configured securely.
- Never commit API keys, access tokens, passwords, or private financial data.
- Verify Python and dependency versions.
- Confirm FAQ and knowledge-base files are present and use UTF-8 encoding.
- Run focused retrieval and chatbot regression tests.
- Run the complete pytest suite.
- Review test failures and warnings before deployment.
- Confirm backend connectivity and session isolation in the target environment.

## 3. Deployment Procedure
1. Obtain approval for the deployment candidate.
2. Review code changes and configuration differences.
3. Install dependencies from the approved dependency specification.
4. Configure secrets through the approved deployment secret manager.
5. Run the test suite in the deployment environment.
6. Deploy using the organization's approved deployment process.
7. Execute health checks and approved smoke tests.
8. Verify authentication, session boundaries, and financial data access.
9. Record deployment version, date, test results, and responsible owner.

Do not treat local pytest success as proof of production readiness.

## 4. Monitoring
Monitor and record:
- Request outcomes and error categories.
- Retrieval success and empty-result rates.
- Retrieved source identifiers.
- Response latency.
- Embedding and LLM provider failures.
- Provider usage and estimated costs.
- Authentication and authorization failures.

Logs must not contain API keys, tokens, passwords, or private financial information.

## 5. Maintenance
- Review weak and failed evaluation queries.
- Update knowledge-base content only after source verification.
- Re-run retrieval tests after changes to FAQ data or retrieval configuration.
- Review dependency and model compatibility.
- Preserve approved backups before modifying important data or model artifacts.
- Document every configuration or model change.

## 6. Incident Response
1. Record the incident time and affected component.
2. Capture safe diagnostic information without secrets or private financial data.
3. Determine whether the issue affects retrieval, authentication, backend access, or provider availability.
4. Escalate production financial-data or session-isolation issues to the responsible team.
5. Apply only an approved fix or rollback.
6. Re-run relevant tests and document the outcome.

## 7. Rollback
- Use the last approved deployment version.
- Restore configuration from the approved backup.
- Verify service health and access boundaries after rollback.
- Record the reason, version, and verification results.

## 8. Current Verification Limitations
The following are not yet independently verified:
- Production financial backend connectivity.
- Production session isolation.
- Complete multi-turn financial workflows.
- Citation rendering and source-conflict behavior.
- End-to-end latency and provider costs.

## 9. Operational Status
This runbook documents a recommended procedure. It does not confirm that a production deployment, production monitoring setup, or rollback exercise has been performed.
