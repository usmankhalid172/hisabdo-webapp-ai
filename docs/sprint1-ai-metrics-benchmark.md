# Sprint 1 AI Metrics Benchmark Evaluation

## 1. Objective

This benchmark establishes baseline evaluation metrics for the AI chatbot response pipeline.

The evaluation covers:

1. JSON output validity
2. Model response latency
3. Response consistency across executions
4. Symptom extraction accuracy

## 2. Evaluation Environment

- Project: HisabDo Web App AI
- Evaluation date: 2026-09-05
- Execution mode: Local development environment
- LLM provider: MockLLMProvider
- Benchmark script: `tests/ai_metrics_benchmark.py`
- Consistency validator: `tests/output_consistency_validator.py`

## 3. Metrics and Results

### 3.1 JSON Output Validity

Three chatbot responses were evaluated for valid response schema and JSON serialization.

| Test | Result |
|---|---|
| JSON-LAT-01 | PASS |
| JSON-LAT-02 | PASS |
| JSON-LAT-03 | PASS |

- Total responses: 3
- Valid responses: 3
- JSON validity rate: **100.00%**

The responses successfully passed `ChatbotResponse` validation and JSON serialization checks.

### 3.2 Response Latency

The benchmark measured execution time using `time.perf_counter()`.

| Test | Latency |
|---|---:|
| JSON-LAT-01 | 27.66 ms |
| JSON-LAT-02 | 1.41 ms |
| JSON-LAT-03 | 0.56 ms |

Summary:

- Average latency: **9.88 ms**
- Minimum latency: **0.56 ms**
- Maximum latency: **27.66 ms**

These values represent local MockLLM/application execution and should not be treated as production external-LLM latency.

### 3.3 Response Consistency

The existing LLM output consistency validator executed five test cases across three cycles, producing 15 total executions.

| Metric | Result |
|---|---:|
| Total executions | 15 |
| Passed | 12 |
| Flagged | 3 |
| Validation pass rate | **80.00%** |
| Flag rate | **20.00%** |

TC-01 through TC-04 were consistent across all three cycles.

TC-05 produced invalid-output flags across its three cycles:

- Cycle 1: Empty response
- Cycle 2: Response contains no usable content
- Cycle 3: Response is a bare echo of the question

This identifies a consistency/response-quality edge case that requires further investigation.

### 3.4 Symptom Extraction Accuracy

**Status: N/A — Not Implemented**

No symptom extraction component or corresponding ground-truth evaluation dataset was identified in the current chatbot implementation.

Therefore, no accuracy percentage is reported for this metric. Future evaluation should define a labeled test dataset containing expected symptom entities before calculating extraction accuracy.

## 4. Baseline Summary

| Metric | Baseline |
|---|---:|
| JSON output validity | **100.00%** |
| Average response latency | **9.88 ms** |
| Minimum latency | **0.56 ms** |
| Maximum latency | **27.66 ms** |
| Response consistency validation pass rate | **80.00%** |
| Symptom extraction accuracy | **N/A — Not Implemented** |

## 5. Findings

1. All three benchmark responses produced valid chatbot response objects and JSON-serializable output.
2. Local benchmark latency was low, with an average of 9.88 ms.
3. The first RAG-related benchmark response had the highest measured latency at 27.66 ms.
4. Four consistency test cases passed across all three executions.
5. TC-05 exposed three invalid-output conditions and resulted in the overall 80.00% validation pass rate.
6. Symptom extraction accuracy cannot currently be measured because the required extraction component and labeled evaluation data are not implemented.

## 6. Recommendations

- Investigate the TC-05 invalid-output behavior.
- Repeat latency testing with multiple executions per test case for a more stable latency baseline.
- Add a labeled symptom extraction dataset if symptom extraction becomes part of the implemented AI functionality.
- Repeat these benchmarks after major model, prompt, or integration changes to compare performance against this baseline.

## 7. Conclusion

The Sprint 1 benchmark establishes an initial measurable baseline for AI response quality and performance.

The current implementation achieved **100.00% JSON output validity** in the benchmark sample, an average local execution latency of **9.88 ms**, and an **80.00% response consistency validation pass rate**. The consistency failures provide a clear QA follow-up area, while symptom extraction remains not applicable until the feature is implemented and test data is available.
