@"
# Sprint 1 AI Metrics Benchmark

## Evaluation Summary

- Evaluation date: 2026-09-12
- Environment: Local development environment
- LLM provider: MockLLMProvider
- Endpoint: POST /api/v1/chatbot
- Total HTTP tests: 10
- HTTP 200 responses: 10
- Valid JSON responses: 10
- JSON validity rate: 100.00%
- Average API latency: 18.50 ms
- Minimum API latency: 6.76 ms
- Maximum API latency: 99.82 ms

## Individual Latency Results

| Test ID | HTTP Status | JSON Valid | Latency |
|---|---:|---|---:|
| HTTP-LAT-01 | 200 | True | 99.82 ms |
| HTTP-LAT-02 | 200 | True | 9.99 ms |
| HTTP-LAT-03 | 200 | True | 10.34 ms |
| HTTP-LAT-04 | 200 | True | 7.56 ms |
| HTTP-LAT-05 | 200 | True | 10.80 ms |
| HTTP-LAT-06 | 200 | True | 9.37 ms |
| HTTP-LAT-07 | 200 | True | 9.80 ms |
| HTTP-LAT-08 | 200 | True | 10.84 ms |
| HTTP-LAT-09 | 200 | True | 6.76 ms |
| HTTP-LAT-10 | 200 | True | 9.73 ms |

## Benchmark Notes

The benchmark was regenerated through the HTTP API layer using
POST /api/v1/chatbot. This covers API routing, authentication,
HTTP status validation, response serialization, JSON validity,
and end-to-end local API latency.

Latency values are end-to-end local HTTP API timings using TestClient.
They include API/client overhead and should not be interpreted as
production external LLM latency.

The latest benchmark run supersedes the earlier 3-case direct
service-layer latency measurements.

## Response Consistency

- Total executions: 15
- Passing executions: 12
- Flagged executions: 3
- Consistency rate: 80.00%

TC-05 was flagged in all three cycles because of inconsistent or
unusable response content. The findings are retained for follow-up
improvement rather than being hidden from the benchmark.

## Symptom Extraction Accuracy

N/A - Symptom extraction is not currently implemented in the
available chatbot evaluation flow.

## Reproducibility

Run the benchmark with:

    python -m tests.ai_metrics_benchmark

## Findings

1. JSON response validity was 100% across all 10 HTTP API tests.
2. All 10 benchmark requests returned HTTP 200.
3. The benchmark now exercises the HTTP API layer instead of only
   calling the service layer directly.
4. Local API latency varies between runs because this is a local
   development environment.
5. Response consistency requires further investigation for TC-05.
6. Symptom extraction accuracy cannot currently be measured because
   symptom extraction is not implemented.
"@ | Set-Content "docs/sprint1-ai-metrics-benchmark.md"

@"
=== Sprint 1 AI Metrics Benchmark ===
Evaluation date: 2026-09-12
Endpoint: POST /api/v1/chatbot
LLM provider: MockLLMProvider
Execution mode: Local development environment

Total HTTP tests: 10
HTTP 200 responses: 10
Valid JSON responses: 10
JSON validity rate: 100.00%
Average API latency: 18.50 ms
Minimum API latency: 6.76 ms
Maximum API latency: 99.82 ms

--- Individual Results ---
{'test_id': 'HTTP-LAT-01', 'http_status': 200, 'json_valid': True, 'latency_ms': 99.82}
{'test_id': 'HTTP-LAT-02', 'http_status': 200, 'json_valid': True, 'latency_ms': 9.99}
{'test_id': 'HTTP-LAT-03', 'http_status': 200, 'json_valid': True, 'latency_ms': 10.34}
{'test_id': 'HTTP-LAT-04', 'http_status': 200, 'json_valid': True, 'latency_ms': 7.56}
{'test_id': 'HTTP-LAT-05', 'http_status': 200, 'json_valid': True, 'latency_ms': 10.8}
{'test_id': 'HTTP-LAT-06', 'http_status': 200, 'json_valid': True, 'latency_ms': 9.37}
{'test_id': 'HTTP-LAT-07', 'http_status': 200, 'json_valid': True, 'latency_ms': 9.8}
{'test_id': 'HTTP-LAT-08', 'http_status': 200, 'json_valid': True, 'latency_ms': 10.84}
{'test_id': 'HTTP-LAT-09', 'http_status': 200, 'json_valid': True, 'latency_ms': 6.76}
{'test_id': 'HTTP-LAT-10', 'http_status': 200, 'json_valid': True, 'latency_ms': 9.73}

Note: Latency values are end-to-end local HTTP API timings using TestClient
and include API/client overhead. They are not production external LLM latency.

Reproducibility command:
python -m tests.ai_metrics_benchmark
"@ | Set-Content "docs/sprint1-ai-metrics-benchmark-log.txt"