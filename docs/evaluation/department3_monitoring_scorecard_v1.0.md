# Department 3 Monitoring and Quality Scorecard

## 1. Scope
Monitoring and retrieval quality review for the HisabDo Department 3 financial assistant.

## 2. Before/After Quality Scorecard

| Metric | Before / Existing Baseline | Current Measurement | Status |
|---|---:|---:|---|
| Verified evaluation questions | 41 | 41 | Same dataset |
| Expected source matches | 30 | 30 | No measured improvement |
| Retrieval source-match rate | 73.17% | 73.17% | Unchanged |
| Answer accuracy | Not independently measured | Not independently measured | Pending |
| Relevance score | Not independently measured | Not independently measured | Pending |
| Completeness score | Not independently measured | Not independently measured | Pending |
| Citation correctness | Not independently measured | Not independently measured | Pending |

Source matching measures whether at least one expected source ID was retrieved. It does not establish answer accuracy or completeness.

## 3. Current Retrieval Latency

Measured using 41 verified questions from department3_evaluation_set_v1.0.csv. One warm-up retrieval was excluded.

| Metric | Result |
|---|---:|
| Successful retrievals | 35 |
| Empty retrievals | 6 |
| Average latency | 18.47 ms |
| Median (p50) | 18.47 ms |
| p95 latency | 21.07 ms |
| Maximum latency | 21.37 ms |

These values represent local FAQ retrieval only, not end-to-end chatbot or external provider latency.

Detailed measurements: department3_latency_benchmark.csv

## 4. Monitoring and Error Coverage

The monitoring implementation records:
- Chat request outcomes and latency.
- Retrieval success, empty results and retrieved source IDs.
- Provider name, model, token usage when supplied by the provider, and latency.
- Index update success or failure.
- Error categories and in-process counters.

Available counters:
requests, success, fallback, blocked, errors, retrieval_empty, retrieval_success, index_update_failures, provider_failures, backend_failures.

## 5. Privacy-Safe Logging Fields

| Field | Purpose |
|---|---|
| event | Allowlisted event name |
| component | Chat, retrieval, provider, backend or index |
| outcome | Success, fallback, blocked or error |
| latency_ms | Operation duration |
| provider | Allowlisted provider |
| model | Allowlisted model |
| input_tokens | Provider-reported input token count |
| output_tokens | Provider-reported output token count |
| retrieved_source_ids | Validated source identifiers |
| error_category | Allowlisted error classification |

Never log:
- User questions or chatbot response text.
- Customer names, user identifiers or account numbers.
- Financial balances, transaction descriptions or amounts.
- API keys, passwords, authorization headers or access tokens.
- Raw exception messages, tracebacks, prompts or private backend payloads.

## 6. Provider Usage and Cost

Provider instrumentation records latency and token usage when actual providers return usage information.

No live external API calls or billing measurements were performed for this benchmark. Therefore, actual provider monetary cost is not available and must not be estimated or presented as measured.

The configured local embedding model does not provide a per-query hosted embedding API cost in this benchmark.

## 7. Limitations and Follow-up

- Current source-match rate remains 73.17%; no measured retrieval quality improvement is established.
- Six of 41 verified questions returned no FAQ results and need investigation.
- Answer accuracy, completeness and citation quality require independent response scoring.
- The latency benchmark is a single local run per question, not a concurrency or load test.
- Monitoring counters are in-memory and reset when the process restarts.
- Production API cost and end-to-end latency require authorized live provider/backend instrumentation.

## 8. Validation Evidence

Focused automated test command:

python -m pytest tests\test_department3_monitoring.py tests\test_chatbot.py tests\test_llm_service.py tests\test_faq_rag.py tests\test_faq_rag_security.py -q

Latest result: 47 passed, 2 dependency/deprecation warnings.

The warnings were not test failures.
