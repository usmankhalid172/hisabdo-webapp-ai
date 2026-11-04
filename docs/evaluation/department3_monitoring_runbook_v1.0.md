# Department 3 Monitoring and Maintenance Runbook

## 1. Purpose

Operational guidance for monitoring, troubleshooting and maintaining the HisabDo Department 3 chatbot retrieval and financial assistant flows.

## 2. Privacy and Logging Rules

Use the monitoring helpers in src/financial_assistant/monitoring.py.

Allowed operational fields:
- event
- component
- outcome
- latency_ms
- provider
- model
- input_tokens
- output_tokens
- retrieved_source_ids
- error_category

Never log raw user queries, responses, financial details, customer identifiers, secrets, authorization tokens, prompts or raw exception details.

Do not enable exception tracebacks in production logs for financial request paths.

## 3. Normal Monitoring

Review the following counters from monitoring_counters.snapshot():

- requests
- success
- fallback
- blocked
- errors
- retrieval_empty
- retrieval_success
- index_update_failures
- provider_failures
- backend_failures

These counters are in-memory. Capture/export snapshots through an approved operational metrics system before relying on them for long-term production reporting.

Review latency by component:
- chat_request
- retrieval
- provider_call
- backend_call
- index_update

Do not interpret local FAQ retrieval latency as end-to-end chatbot latency.

## 4. Empty Retrieval Handling

1. Check retrieval outcome and retrieval_empty counter.
2. Confirm the FAQ knowledge base contains verified documents.
3. Check whether the query is in scope and passes input guardrails.
4. Do not invent an answer or use unverified financial information.
5. Use the application's safe fallback or clarification response.
6. Record only the safe error category and operational metadata.

An empty FAQ retrieval must not be treated as permission to expose another user's financial records.

## 5. FAQ Index Update and Recovery

The FAQ retriever exposes rebuild_index().

To attempt an index rebuild from the application:

    from src.financial_assistant.faq_rag import get_retriever
    success = get_retriever().rebuild_index()

Expected behavior:
- A replacement index is built before swapping.
- An empty or failed replacement is rejected.
- The previous working index is retained if rebuilding fails.
- An index update failure is counted and logged without exception details.

After a successful rebuild, run:

    python -m pytest tests\test_faq_rag.py tests\test_faq_rag_security.py -q

Do not manually delete the existing index or verified knowledge base as a recovery step.

## 6. Backend and Provider Errors

1. Check backend_failures, provider_failures and errors counters.
2. Check safe event metadata, provider name, model and latency.
3. Verify service availability and approved provider configuration.
4. Do not print API keys, tokens, request bodies or raw exception messages.
5. Allow the application safe fallback behavior to respond.
6. Escalate persistent failures to the authorized backend/provider maintainer.

Provider token usage is recorded only when returned by the provider. Monetary cost requires actual provider billing data and approved pricing configuration.

## 7. Knowledge Base Maintenance

1. Review data/faq_docs.json before changing content.
2. Keep verified and unverified records clearly distinguished.
3. Do not promote needs_review records to verified without source validation.
4. Preserve source identifiers and source attribution.
5. Run FAQ retrieval and security tests after changes.
6. Rebuild the index and verify that the previous index remains available if the update fails.

## 8. Benchmark Procedure

Run:

    python docs\evaluation\department3_latency_benchmark.py

The benchmark:
- Uses verified evaluation questions.
- Performs one warm-up retrieval.
- Measures local FAQ retrieval latency.
- Records retrieval outcomes and expected source ID matches.
- Writes detailed CSV and Markdown summary files.

It is not a load test and does not measure full chatbot or external API latency.

## 9. Regression Test Procedure

Run:

    python -m pytest tests\test_department3_monitoring.py tests\test_chatbot.py tests\test_llm_service.py tests\test_faq_rag.py tests\test_faq_rag_security.py -q

Investigate failures before release. Dependency deprecation warnings should be tracked separately from test failures.

## 10. Operational Limitations

- Monitoring counters reset on process restart.
- No persistent metrics exporter is configured by this implementation.
- No live API cost or production end-to-end latency measurement is included in the local benchmark.
- The current verified-source match result is 30/41 (73.17%); six questions returned empty retrieval.
- Independent answer-quality scoring and production load testing remain future work.
