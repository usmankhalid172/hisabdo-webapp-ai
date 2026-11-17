# Department 3 Operational Maintenance and Deployment Runbook

Date: 17 November 2026
Project: HisabDo AI Financial Assistant

## 1. Purpose

This runbook describes the operational checks, maintenance steps, validation process, and deployment restrictions for the Department 3 financial assistant.

Current release status: NOT CLEARED FOR PRODUCTION.

## 2. Current Runtime Overview

Retrieval:
TF IDF with English stop words and cosine similarity.

Relevance threshold:
0.30.

Retrieval limit:
Three documents per API request.

LLM provider:
Mock by default.

Knowledge source:
data/faq_docs.json.

Financial data:
Personal financial values must come from the authenticated backend financial API, never from RAG documents.

## 3. Pre Deployment Checklist

Before any deployment:

1. Confirm the intended Git branch and review all pending changes.
2. Confirm environment configuration.
3. Verify that production secrets are supplied securely.
4. Confirm INTERNAL_SERVICE_TOKEN meets the 32 character minimum.
5. Confirm JWT_SECRET_KEY meets the 32 character minimum and is not weak.
6. Verify the approved LLM provider and its production configuration.
7. Verify the real backend financial API contract.
8. Confirm customer identity and session isolation.
9. Verify approved source metadata and source URLs.
10. Review retrieval and safety configuration changes.
11. Run the full automated test suite.
12. Obtain required security and product approvals.

Do not deploy while required production blockers remain open.

## 4. Validation Commands

Run from the repository root.

Focused regression tests:

python -m pytest tests/test_chatbot.py tests/test_grounded_response_rules.py tests/test_cross_user_data_boundary.py tests/test_integration_api.py -q

Full test suite:

python -m pytest -q

Inspect pending changes:

git status --short

Review the diff before preparing a release:

git diff --check
git diff

Record the actual test counts, skipped tests, warnings, and failures in the release evidence.

## 5. Retrieval Maintenance

Knowledge file:
data/faq_docs.json.

Before updating knowledge records:

1. Validate that the file contains a non empty list.
2. Confirm each record has a title and text.
3. Check IDs for uniqueness.
4. Review category, section, language, and source metadata.
5. Obtain approved source URLs from content owners.
6. Check for duplicate or conflicting content.
7. Run retrieval evaluation against the approved dataset.
8. Compare retrieval results with the recorded POC baseline.

After an approved update, verify retriever initialization and retrieval responses.

The current implementation supports refresh through the retriever refresh method. A failed refresh returns false. Verify the active service state before considering an update successful.

Do not introduce dense embeddings, BM25, hybrid weights, or reranking without a separate implementation and evaluation approval.

## 6. Prompt and Safety Maintenance

Prompt file:
src/financial_assistant/prompts.py.

Safety implementation:
src/financial_assistant/service.py.

When changing prompt or safety rules:

1. Record the reason for the change.
2. Review financial data boundaries.
3. Review prompt injection detection.
4. Review sensitive information protection.
5. Test out of scope and unsafe language behavior.
6. Test ambiguous expense questions.
7. Test missing evidence and source conflicts.
8. Test citation support.
9. Run the related regression tests.
10. Record the result and review approval.

Never put API keys, tokens, passwords, or private credentials in prompts, source files, or reports.

## 7. Financial Data Safety

Personal balances, transactions, and expenses must be obtained only through the authenticated backend financial API.

Never use retrieved FAQ or knowledge documents to answer personal account balance questions.

Verify that missing customer identity is rejected and that one customer's identity cannot access another customer's financial data.

Production session isolation and concurrent customer tests remain outstanding.

## 8. Deployment Procedure

Production deployment is currently blocked.

After all blockers receive approval:

1. Confirm production environment variables through the approved secret management process.
2. Confirm the production LLM provider.
3. Confirm the real backend integration.
4. Confirm approved retrieval and knowledge configuration.
5. Run the full test suite.
6. Complete security and session isolation checks.
7. Obtain release approval.
8. Deploy through the approved deployment pipeline.
9. Verify health and version endpoints.
10. Run authenticated chatbot smoke tests.
11. Review logs for errors and unexpected routing.
12. Record deployment version and verification evidence.

Do not treat local automated tests as proof of production readiness.

## 9. Monitoring and Incident Handling

Review:

1. API errors and response failures.
2. Retrieval empty results and weak matches.
3. Citation completeness.
4. Prompt injection and refusal events.
5. Authentication failures.
6. Backend financial API failures.
7. Unexpected cross customer access attempts.
8. Response latency and provider errors.

If a security or customer data boundary issue is suspected:

1. Stop the affected release or feature through the approved incident process.
2. Preserve relevant logs and evidence securely.
3. Notify the responsible security and backend owners.
4. Do not expose customer financial information in reports.
5. Resume only after investigation and approval.

## 10. Current Outstanding Blockers

1. Approved source URLs are missing from all 12 knowledge records.
2. Hybrid retrieval is not active in the API.
3. Dense embedding performance has not been measured.
4. Production financial backend integration is unverified.
5. Production LLM provider is unvalidated.
6. Production session isolation and concurrent customer tests are outstanding.
7. Full Day 1 golden dataset integrated API validation is incomplete.

## 11. Handover

The current POC baseline and local automated test evidence are documented.

The maintenance owner must coordinate with the product, backend, security, and content owners before production approval.

Release decision: NOT CLEARED.

Deployment authorization: NOT GRANTED.
