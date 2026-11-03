# Department 3 Retrieval Quality and Monitoring Report

## 1. Task Summary

This report records the retrieval improvements, safe fallback behavior, logging changes, evaluation evidence, and maintenance procedures for Department 3 account, balance, and expense components.

## 2. Before and After Quality Scorecard

### Historical baseline

The historical 20 question evaluation recorded:

| Retrieval method | Hit at 1 | Hit at 3 |
|---|---:|---:|
| TF IDF baseline | 68.75% | 93.75% |
| Normalized query | 68.75% | 93.75% |
| Synonym expansion | 81.25% | 93.75% |
| Expansion with reranking | 81.25% | 87.50% |

### Current evaluation

The newer evaluation contains 71 questions and 12 knowledge documents.

| Metric | Current result |
|---|---:|
| Answerable questions | 55 |
| No answer or clarification questions | 16 |
| Hit at 1 on answerable questions | 89.09% |
| Hit at 3 on answerable questions | 96.36% |
| No answer cases that still retrieved a source | 16 of 16 |

The historical and current datasets differ, so their scores must not be treated as a controlled before and after comparison. Retrieval hit rate does not prove final answer accuracy or safe abstention.

### Implemented improvements

1. Empty retrieval returns a safe response instead of calling the LLM without verified context.
2. Retrieval results record safe source identifiers and retrieval duration.
3. Failed index refresh retains the previously active index.
4. Provider failures return safe fallback responses.
5. Expense categorization failures return an Uncategorized result requiring confirmation.
6. Sensitive user and financial information is excluded from the added structured log fields.

A new end to end answer quality score has not yet been measured. It must be evaluated with the approved answer quality rubric.

## 3. Test and Error Metrics

Latest targeted test command:

`python -m pytest tests\test_chatbot.py tests\test_categorization.py tests\test_cross_user_data_boundary.py tests\test_safety_guardrails.py -q`

Result: 43 passed, 0 failed, 1 dependency deprecation warning.

The reported test execution time was 0.16 seconds. This is a local test suite duration, not a production request latency measurement.

Production p50, p95, and p99 response latency have not been measured. External provider API costs have not been measured because the default provider is a deterministic mock and no verified production usage or pricing data was available.

## 4. Latency and Provider Usage Measurement

The request middleware measures total HTTP request duration using a monotonic performance timer.

The chatbot service measures:
1. Retrieval duration.
2. LLM provider call duration.
3. Provider reported token usage when available.

Provider token counts are not equivalent across providers. Some providers return output token counts only. The mock provider uses an approximate word count, not actual tokenization.

For reliable cost reporting, record provider, model, input tokens, output tokens, request count, and the applicable dated provider price per token. Calculate costs only from verified provider usage and pricing records.

Do not estimate production costs from mock token counts.

## 5. Safe Logging Field Definitions

Allowed structured fields:

| Field | Purpose |
|---|---|
| event | Fixed event name |
| request_id | Generated request correlation ID |
| method | HTTP method |
| status_code | HTTP response status |
| duration_ms | Total request duration |
| intent | Classified request intent |
| outcome | Success, empty, unavailable, or error |
| source | Backend, RAG, or fallback source |
| source_ids | Retrieved knowledge document identifiers |
| provider_name | Configured provider name |
| tokens_used | Provider reported token count |
| retrieval_duration_ms | Retrieval execution time |
| provider_duration_ms | Provider call execution time |
| error_category | Safe predefined error category |

Never log passwords, API keys, authorization headers, JWTs, internal service tokens, raw user messages, account identifiers, balances, transaction descriptions, merchant details, or complete financial summaries.

Do not add raw exception messages or stack traces to ordinary application logs. Use fixed error categories such as backend_unavailable, provider_error, model_unavailable, and index_refresh_failed.

## 6. Safe Failure and Fallback Behavior

### Index update failure

Build and validate a replacement index before activating it. If loading or validation fails, retain the previous working index. Record a fixed error category without logging document contents.

### Empty retrieval

Do not generate an answer without verified supporting content. Return the safe no verified information response and record an empty retrieval outcome.

### LLM or API failure

Return a generic temporary unavailable response. Do not expose provider credentials, raw exception details, or internal request data.

### Expense model failure

Return Uncategorized with zero confidence and require user confirmation. Do not silently invent a category.

### Backend financial data failure

Do not substitute mock financial information in production. Return a temporary unavailable response.

## 7. Monitoring and Maintenance Runbook

### Daily checks

1. Review request success and failure counts.
2. Review retrieval empty outcomes.
3. Review provider error categories.
4. Check request and retrieval duration measurements.
5. Check that logs contain no sensitive information.

### Knowledge index update

1. Back up the approved knowledge source.
2. Validate JSON structure and required metadata.
3. Build a candidate index.
4. Run retrieval tests.
5. Activate the new index only after successful validation.
6. Keep the previous working index available for rollback.

### Evaluation

1. Run the Department 3 evaluation dataset.
2. Compare Hit at 1 and Hit at 3 with the recorded baseline.
3. Review no answer and clarification cases separately.
4. Score final responses using the approved quality rubric.
5. Record dataset version and evaluation date.

### Provider monitoring

1. Track provider request counts and reported token usage.
2. Track provider call duration and error categories.
3. Obtain verified input and output token pricing before calculating costs.
4. Never record API keys or authorization tokens.

### Incident response

1. Identify the affected component using the event and request ID.
2. Check the error category and safe timing metrics.
3. Confirm whether the fallback response was returned.
4. Restore the last valid knowledge index if an update failed.
5. Rerun the relevant tests before closing the incident.

## 8. Known Limitations

1. Current retrieval scores measure document retrieval, not final answer correctness.
2. No production traffic latency distribution is available.
3. No verified external provider cost data is available.
4. The production financial backend is not configured in the inspected development setup.
5. The local test suite does not replace production monitoring.
6. A controlled answer quality before and after evaluation remains necessary.

## 9. Final Status

Implemented and tested: safe retrieval fallback, index refresh protection, provider error handling, expense categorization fallback, request timing, retrieval timing, provider timing, and structured safe logging.

Validation evidence: 43 targeted tests passed with no failures.

Pending production evidence: real traffic latency percentiles, external provider usage costs, and a comparable end to end answer quality scorecard.
