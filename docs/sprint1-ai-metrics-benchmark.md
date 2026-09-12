# Sprint 1 AI Metrics Benchmark Evaluation

## 1. Objective

This benchmark establishes baseline evaluation metrics for the AI chatbot response pipeline.

The evaluation covers:

1. JSON output validity
2. Model response latency
3. Response consistency across executions
4. Symptom extraction accuracy

## 2. Evaluation Environment

* Project: HisabDo Web App AI
* Evaluation date: 2026-09-12
* Execution mode: Local development environment
* LLM provider: MockLLMProvider
* Benchmark script: `tests/ai_metrics_benchmark.py`
* Consistency validator: `tests/output_consistency_validator.py`
* API endpoint: `POST /api/v1/chatbot`

The benchmark was regenerated using the HTTP API layer rather than calling the chatbot service directly. This provides coverage of API routing, authentication, HTTP status handling, and response serialization.

The reproducible benchmark command is:

```text
python -m tests.ai_metrics_benchmark
```

## 3. Metrics and Results

### 3.1 JSON Output Validity

Ten chatbot requests were evaluated through the `/api/v1/chatbot` HTTP endpoint.

| Metric               |      Result |
| -------------------- | ----------: |
| Total requests       |          10 |
| HTTP 200 responses   |          10 |
| Valid JSON responses |          10 |
| JSON validity rate   | **100.00%** |

All benchmark requests returned HTTP 200 responses with JSON response bodies.

### 3.2 Response Latency

Response latency was measured using `time.perf_counter()` around the HTTP API request.

| Test        |   Latency |
| ----------- | --------: |
| HTTP-LAT-01 | 158.89 ms |
| HTTP-LAT-02 |  30.47 ms |
| HTTP-LAT-03 |   9.87 ms |
| HTTP-LAT-04 |   9.46 ms |
| HTTP-LAT-05 |   8.32 ms |
| HTTP-LAT-06 |   9.86 ms |
| HTTP-LAT-07 |   9.70 ms |
| HTTP-LAT-08 |   7.90 ms |
| HTTP-LAT-09 |   8.16 ms |
| HTTP-LAT-10 |   8.22 ms |

Summary:

* Average API latency: **26.08 ms**
* Minimum latency: **7.90 ms**
* Maximum latency: **158.89 ms**

These measurements represent local HTTP API execution using `MockLLMProvider`. They should not be interpreted as production external-LLM latency.

The current benchmark supersedes the earlier 3-case direct service-layer latency measurements. The new baseline uses 10 HTTP API requests to provide broader endpoint coverage and consistent measurement methodology.

### 3.3 Response Consistency

The existing LLM output consistency validator executed five test cases across three cycles, producing 15 total executions.

| Metric               |     Result |
| -------------------- | ---------: |
| Total executions     |         15 |
| Passed               |         12 |
| Flagged              |          3 |
| Validation pass rate | **80.00%** |
| Flag rate            | **20.00%** |

TC-01 through TC-04 were consistent across all three cycles.

TC-05 produced invalid-output flags across its three cycles:

* Cycle 1: Empty response
* Cycle 2: Response contains no usable content
* Cycle 3: Response is a bare echo of the question

This identifies a response-quality edge case that requires further investigation.

### 3.4 Symptom Extraction Accuracy

**Status: N/A — Not Implemented**

No symptom extraction component or corresponding ground-truth evaluation dataset was identified in the current chatbot implementation.

Therefore, no accuracy percentage is reported for this metric.

If symptom extraction becomes part of the implemented AI functionality, a labeled evaluation dataset containing expected symptom entities should be created before calculating extraction accuracy.

## 4. Baseline Summary

| Metric                                    |                  Baseline |
| ----------------------------------------- | ------------------------: |
| JSON output validity                      |               **100.00%** |
| HTTP 200 response rate                    |               **100.00%** |
| Average API latency                       |              **26.08 ms** |
| Minimum latency                           |               **7.90 ms** |
| Maximum latency                           |             **158.89 ms** |
| Response consistency validation pass rate |                **80.00%** |
| Symptom extraction accuracy               | **N/A — Not Implemented** |

## 5. Findings

1. All 10 benchmark requests returned successful HTTP 200 responses with valid JSON output.

2. JSON output validity was **100.00%** across the benchmark sample.

3. Average HTTP API latency was **26.08 ms**, with a minimum of **7.90 ms** and a maximum of **158.89 ms**.

4. The benchmark now exercises the actual `/api/v1/chatbot` HTTP endpoint rather than only calling the internal chatbot service layer.

5. The HTTP benchmark provides coverage of API routing, authentication, HTTP response status, and JSON response handling.

6. Response consistency validation achieved an **80.00% pass rate**. TC-01 through TC-04 were consistent, while TC-05 was flagged across all three cycles.

7. Symptom extraction accuracy remains unavailable because the feature and labeled evaluation dataset are not currently implemented.

## 6. Recommendations

* Investigate and improve the TC-05 invalid-output behavior.
* Repeat latency testing with multiple cycles per test case for a more stable performance baseline.
* Expand benchmark coverage with additional realistic chatbot requests.
* Add dedicated API-level validation for authentication failures and invalid request payloads in future benchmark iterations.
* Add a labeled symptom extraction dataset if symptom extraction becomes part of the implemented AI functionality.
* Repeat these benchmarks after major model, prompt, RAG, or API integration changes to compare performance against the baseline.

## 7. Conclusion

The Sprint 1 benchmark establishes an updated measurable baseline for AI response quality and performance using the actual chatbot HTTP API endpoint.

The current implementation achieved **100.00% JSON output validity** across 10 benchmark requests, with an average local API latency of **26.08 ms** and an **80.00% response consistency validation pass rate**.

The benchmark also identified TC-05 as a response-quality edge case requiring further investigation. Symptom extraction remains not applicable until the feature and corresponding evaluation dataset are implemented.

The benchmark results should be treated as a local development baseline using `MockLLMProvider`, not as production external-LLM performance.
