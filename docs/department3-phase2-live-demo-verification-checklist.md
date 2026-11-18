# Department 3 — Live Demo Verification Checklist

**Date:** 18 November 2026
**Environment verified:** Local development environment
**Production demo status:** Not verified

## Local checks completed
- [x] Python environment identified (Python 3.12.10).
- [x] Required application and data files found.
- [x] Application routes imported and inspected.
- [x] GET `/api/v1/health` returned HTTP 200.
- [x] GET `/api/v1/version` returned HTTP 200; provider reported as `mock`.
- [x] Focused test run: 104 passed, 41 warnings.
- [x] Additional focused test run: 78 passed, 1 warning.
- [x] Retrieval demo executed and returned ranked results.

## Demonstration capabilities supported by local tests
- [x] FAQ retrieval and context formatting.
- [x] Grounded context passed to the LLM service in tested paths.
- [x] Intent recognition and follow-up extraction.
- [x] Conversation-history forwarding.
- [x] Tested prompt-injection and oversized-input guardrails.
- [x] Tested authentication and cross-user boundary cases.

## Not verified — do not demonstrate as production-proven
- [ ] Live production deployment and production endpoint.
- [ ] Real financial backend; inspected factory currently returns MockBackendClient.
- [ ] Real customer-account/session isolation.
- [ ] Complete multi-turn financial transaction workflow.
- [ ] Financial chatbot UI inline citation rendering and source-conflict handling.
- [ ] End-to-end LLM/network/backend latency and provider cost.
- [ ] Production monitoring, alerting, backup, and rollback exercise.
- [ ] Stakeholder walkthrough and acceptance.

## Demo safety
Use synthetic/demo data only. Do not enter real customer financial information, credentials, API keys, or tokens. Clearly label mock responses and local test results.

**Verifier:** ____________________
**Date:** ____________________
**Notes / evidence reference:** ____________________
