# Department 3 — Monitoring, Quality Scorecard & Maintenance Runbook

**Intern:** Purnoor Zafar  
**Organization:** XICTEK Systems  
**Project:** HisabDo AI Business Assistant  
**Department:** 3 — Account, Balance & Expense Components  
**Task Date:** 3 November 2026  
**Repository:** `usmankhalid172/hisabdo-webapp-ai`  
**Branch:** `purnoor-zafar-ai-intern`

## 1. Objective

Improve the reliability and observability of Department 3 financial retrieval flows. Review retrieval quality, measure local response performance, reduce sensitive logging risks, and document safe fallback behavior and maintenance procedures.

## 2. Before/After Quality Scorecard

| Metric | Before | After | Evidence / Notes |
|---|---:|---:|---|
| Full test suite | 350 passed, 4 skipped, 1 failed | 353 passed, 4 skipped | Final run: 7.28 seconds; 4 warnings |
| Retrieval evaluation | 10/10 passed | 10/10 passed | Needs review: 0 |
| Ambiguous balance query | Safe no-match behavior | Safe no-match behavior | Clarification handled by chat service |
| Unsupported QuickBooks query | No FAQ match | No FAQ match | No unsupported FAQ answer retrieved |
| Sensitive LLM error logging | Exception message could be exposed | Exception message excluded from updated LLM service logs | Regression tests added |
| Chat-flow observability | No dedicated per-flow metrics | Intent, source, outcome, latency and token metadata logged | Sensitive message/context excluded |
| Embedding initialization failure | TF-IDF fallback existed | Fallback retained and error type logged | No exception message logged |
| Query embedding failure | Empty result returned silently | Empty result returned with safe error-type log | General response path remains available |

The earlier baseline failure was the deterministic safety question about credentials/authentication. A guardrail pattern was added and its targeted test passed. The final suite confirms the current working tree passes the executed tests.

Retrieval quality was already 10/10 before this task. No unsupported retrieval change was made merely to create an apparent improvement.

## 3. Performance and Provider Usage

Measurements were collected in the local development environment using the mock LLM provider and TF-IDF retrieval.

| Measurement | Local result |
|---|---:|
| Average FAQ retrieval latency | 1.016 ms |
| Maximum FAQ retrieval latency | 1.340 ms |
| Average end-to-end FAQ response latency | 1.243 ms |
| Maximum end-to-end FAQ response latency | 1.345 ms |
| OpenAI API key configured | No |
| Active LLM provider | Mock |
| Local external API usage cost | $0 |

**Limitation:** These figures are local mock/TF-IDF measurements. They are not production API latency, provider billing, or live backend performance measurements. Production embedding and LLM usage costs remain unverified.

## 4. Safe Logging Field Definitions

The updated JSON formatter supports the following approved operational metadata fields:

| Field | Purpose | Logging rule |
|---|---|---|
| timestamp | Event time | Allowed |
| level | Severity | Allowed |
| logger | Logger name | Allowed |
| message | Static event description | Must not contain user content |
| request_id | Request correlation | Allowed; do not use as an authentication token |
| path | Request route | Allowed; avoid sensitive query strings |
| method | HTTP method | Allowed |
| status_code | HTTP response status | Allowed |
| duration_ms | Request duration | Allowed |
| intent | Classified chatbot intent | Allowed |
| source | Response source, such as RAG or backend financial API | Allowed |
| outcome | Success, no-match, or error | Allowed |
| retrieved_source_id | FAQ source identifier | Allowed |
| latency_ms | Chat-flow duration | Allowed |
| tokens_used | Provider-reported token count | Allowed as usage metadata |
| error_category | Exception class name | Allowed; never include exception text |

### Prohibited log content

Never log:
- User messages or conversation history.
- User IDs or personally identifying account details.
- Balance, expense, revenue, receivable, or transaction values.
- Financial summaries or retrieved document text.
- API keys, passwords, authorization tokens, or internal secrets.
- Raw provider exception messages or full tracebacks in the financial chat logging path.

The chat-flow logger uses static event names and metadata only. LLM service warnings record exception class names rather than exception messages. The JSON formatter records the exception class when exception information is supplied, not the traceback text.

## 5. Monitoring Events and Metrics

| Event | Recorded information | Expected interpretation |
|---|---|---|
| `request_handled` | Request ID, route, method, status and duration | HTTP request completed |
| `financial_chat_completed` | Intent, source, outcome, latency and tokens | Chat flow completed |
| `financial_chat_failed` | Outcome, latency and error category | Chat flow raised an exception |
| `financial_rag_retrieval` | Retrieved source ID and match/no-match outcome | FAQ retrieval result |
| Embedding initialization warning | Exception type | TF-IDF fallback activated |
| Query embedding warning | Exception type | No FAQ matches returned |

Operational review should compare request latency, chat-flow latency, HTTP error rates, error categories, retrieval no-match frequency, and token usage over time.

No production dashboard, alert thresholds, or persistent metrics aggregation has been verified as deployed.

## 6. Safe Fallback and Failure Behavior

| Failure condition | Current behavior | Limitation / maintenance action |
|---|---|---|
| Embedding initialization fails | Logs exception type and initializes TF-IDF fallback | Verify fallback retrieval quality |
| Query embedding fails | Logs exception type and returns no FAQ matches | General LLM path may be used; monitor no-match/error rates |
| Empty retrieval | No FAQ context is passed to the general LLM path | Verify unsupported questions do not receive invented product facts |
| Ambiguous balance query | Returns a clarification without retrieving an FAQ | Preserve this privacy-safe behavior |
| Personal financial query | Routes to backend financial API, not shared FAQ RAG | Current backend client is a mock; verify real authenticated integration separately |
| LLM/provider error | Chat-flow error is logged and exception is re-raised; generic API handler returns a safe internal error response | A dedicated user-friendly provider fallback is not yet verified |
| Persistent index update failure | No production index-update mechanism exists in the inspected in-memory/demo implementation | Production index rebuild, rollback and recovery require backend/index integration |

Do not describe the mock backend or local fallback as a verified production integration.

## 7. Monitoring and Maintenance Runbook

### Routine checks

1. Confirm the application starts and health endpoint responds.
2. Run the full automated test suite.
3. Run the retrieval evaluation and record passed/needs-review counts.
4. Review structured logs for request failures, chat-flow errors and embedding warnings.
5. Check latency and token usage trends without inspecting user financial content.
6. Confirm that financial questions still route to the authenticated backend path rather than FAQ RAG.
7. Confirm ambiguous balance questions still request clarification.
8. Review no-match and provider-error cases for safe response behavior.

### On embedding initialization failure

1. Check that the configured embedding provider and environment are available.
2. Inspect the exception category, not secret values or raw request content.
3. Confirm TF-IDF fallback initializes successfully.
4. Run retrieval evaluation.
5. Record the fallback event and escalate persistent provider failures.

### On retrieval no-match or quality regression

1. Record the evaluation question ID and expected source ID in the test report.
2. Check FAQ document IDs and metadata.
3. Inspect retrieval scores and source mapping using test fixtures.
4. Confirm ambiguous and unsupported questions remain no-match cases.
5. Re-run the retrieval evaluation after any approved content or retrieval change.

### On LLM/API errors

1. Record request ID, route, status, latency and exception category.
2. Do not copy API keys, authorization headers, prompts, financial summaries or raw exception messages into logs.
3. Check provider configuration and service availability through approved operational channels.
4. Verify the generic error response does not disclose internal exception details.
5. Re-run the relevant provider and chatbot tests after a fix.

### On index update failures

The inspected local implementation does not provide a production persistent-index update workflow. Before production deployment, the owning team must define index versioning, validation, atomic activation, rollback, and recovery procedures.

## 8. Final Verification Evidence

| Check | Result |
|---|---|
| Targeted chatbot and LLM service tests | 33 passed |
| Full test suite | 353 passed, 4 skipped, 4 warnings |
| Full suite runtime | 7.28 seconds |
| Retrieval evaluation | 10/10 passed |
| Retrieval cases needing review | 0 |
| `git diff --check` | One existing trailing blank-line warning in `tests/test_llm_service.py` |
| Production API cost/latency | Not measured |
| Production index update workflow | Not present in inspected implementation |

## 9. Remaining Limitations

- The backend financial client currently returns mock/demo data.
- Live production API latency and provider billing have not been measured.
- A persistent production index update and rollback mechanism was not found.
- A dedicated friendly fallback for provider failures has not been implemented or verified in the financial chat service.
- Persistent metrics aggregation, dashboards and alerting have not been verified.
- Four test warnings remain and should be reviewed separately.

## 10. Conclusion

Department 3 retrieval evaluation remains at 10/10 passing checks. The final automated test suite passed with 353 passed and 4 skipped. Safe metadata logging and chat-flow latency instrumentation were added, and local mock/TF-IDF performance measurements were recorded.

This report distinguishes verified local test evidence from production capabilities that remain unverified. Documentation is prepared for review; Git commit and push require explicit approval.
