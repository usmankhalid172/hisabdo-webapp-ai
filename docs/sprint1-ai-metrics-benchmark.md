# Sprint 1 AI Metrics Benchmark

## Evaluation Summary

- Evaluation date: 2026-09-13
- Environment: Local development environment
- LLM provider: MockLLMProvider
- Endpoint: POST /api/v1/chatbot
- Sequential HTTP tests: 10
- Concurrent HTTP tests: 10
- Concurrent workers: 5

## Sequential HTTP API Benchmark

- Total requests: 10
- HTTP 200 responses: 10
- Successful response rate: 100.00%
- Schema-valid responses: 10
- JSON schema validity rate: 100.00%
- Average latency: 22.31 ms
- Minimum latency: 6.73 ms
- Maximum latency: 148.39 ms

### Individual Sequential Results

| Test ID | HTTP Status | JSON Schema Valid | Latency |
|---|---:|---|---:|
| HTTP-LAT-01 | 200 | True | 148.39 ms |
| HTTP-LAT-02 | 200 | True | 11.44 ms |
| HTTP-LAT-03 | 200 | True | 8.38 ms |
| HTTP-LAT-04 | 200 | True | 7.11 ms |
| HTTP-LAT-05 | 200 | True | 9.44 ms |
| HTTP-LAT-06 | 200 | True | 6.73 ms |
| HTTP-LAT-07 | 200 | True | 9.53 ms |
| HTTP-LAT-08 | 200 | True | 7.10 ms |
| HTTP-LAT-09 | 200 | True | 7.86 ms |
| HTTP-LAT-10 | 200 | True | 7.13 ms |

## Concurrent Multi-User Throughput Benchmark

- Total requests: 10
- Concurrent workers: 5
- HTTP 200 responses: 10
- Successful response rate: 100.00%
- Schema-valid responses: 10
- JSON schema validity rate: 100.00%
- Average latency: 28.37 ms
- Minimum latency: 25.93 ms
- Maximum latency: 34.76 ms
- Concurrent batch duration: 0.0638 seconds
- Throughput: 156.82 requests/second

### Individual Concurrent Results

| Test ID | HTTP Status | JSON Schema Valid | Latency |
|---|---:|---|---:|
| HTTP-CON-01 | 200 | True | 26.21 ms |
| HTTP-CON-02 | 200 | True | 26.60 ms |
| HTTP-CON-03 | 200 | True | 34.76 ms |
| HTTP-CON-04 | 200 | True | 28.28 ms |
| HTTP-CON-05 | 200 | True | 27.73 ms |
| HTTP-CON-06 | 200 | True | 32.38 ms |
| HTTP-CON-07 | 200 | True | 26.25 ms |
| HTTP-CON-08 | 200 | True | 27.22 ms |
| HTTP-CON-09 | 200 | True | 28.36 ms |
| HTTP-CON-10 | 200 | True | 25.93 ms |

## Benchmark Notes

The benchmark was executed through the HTTP API layer using
POST /api/v1/chatbot. This covers API routing, authentication,
HTTP status validation, response serialization, JSON schema
validation, and end-to-end local API latency.

Latency values are end-to-end local HTTP API timings using
FastAPI TestClient. They include local client/API overhead and
should not be interpreted as production external LLM latency.

The sequential benchmark uses 10 distinct chatbot messages,
improving the previous 3-case baseline.

The first sequential request took 148.39 ms, which increases the
sequential average. The remaining sequential requests were between
6.73 ms and 11.44 ms.

The concurrent benchmark uses 5 worker threads and 10 requests
across separate benchmark user IDs to simulate consecutive
multi-user API calls.

## Response Consistency

- Total executions: 15
- Passing executions: 12
- Flagged executions: 3
- Consistency rate: 80.00%

TC-05 was flagged in all three consistency cycles because of
inconsistent or unusable response content. The finding is retained
for follow-up improvement and is not hidden from the benchmark.

## Symptom Extraction Accuracy

N/A - Symptom extraction is not currently implemented in the
available chatbot evaluation flow.

## Reproducibility

Run the benchmark with:

    python -m tests.ai_metrics_benchmark

## Findings

1. JSON schema validity was 100% across all 20 HTTP API benchmark requests.
2. All 20 benchmark requests returned HTTP 200.
3. The benchmark now exercises the HTTP API layer instead of only
   calling the service layer directly.
4. The sequential benchmark was expanded from 3 cases to 10 cases.
5. Concurrent testing achieved 156.82 requests/second in the local
   MockLLM/TestClient environment.
6. Local latency varies between runs because this is a development
   environment.
7. Response consistency requires further investigation for TC-05.
8. Symptom extraction accuracy cannot currently be measured because
   symptom extraction is not implemented.