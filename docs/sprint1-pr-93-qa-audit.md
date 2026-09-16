# Sprint 1 AI QA Audit — PR #93

## PR Information

- **PR:** #93
- **Title:** Add Sprint 1 AI Metrics Benchmark
- **Author:** rimshamushtaq925-dotcom
- **Head Commit Tested:** `1e44aa9139716910f3fcc36d691d3caecf96ca20`
- **QA Branch:** `feature/sprint1-ai-qa-isma`
- **QA Decision:** **REQUEST CHANGES**

## QA Scope

Reviewed the PR for:

- AI chatbot API contract compliance
- Response schema and JSON validity
- Authentication behavior
- Request validation
- Existing categorization API regression
- Benchmark reproducibility and methodology
- Response consistency evidence
- Code/import behavior

## Independent Environment

- OS: Windows
- Python: 3.14.6
- FastAPI/Pydantic/scikit-learn dependencies: available
- LLM provider: Mock/local provider
- PR tested from the PR head commit listed above

## Test Results

### 1. Benchmark Execution

Command:

`python tests/ai_metrics_benchmark.py`

Result:

**FAIL — `ModuleNotFoundError: No module named 'src'`**

The benchmark could not be executed directly as a script from the repository root.

The module form was then tested:

`python -m tests.ai_metrics_benchmark`

### 2. Benchmark Run 1

- Total cases: 3
- Valid JSON: 3/3
- JSON validity: 100%
- Average latency: 12.06 ms
- Minimum latency: 0.04 ms
- Maximum latency: 34.27 ms

### 3. Benchmark Run 2

- Total cases: 3
- Valid JSON: 3/3
- JSON validity: 100%
- Average latency: 11.71 ms
- Minimum latency: 0.04 ms
- Maximum latency: 33.37 ms

The repeated runs confirm JSON validity, but the latency values differ from the submitted evidence.

### 4. Submitted Evidence Consistency Check

The PR description/log reports:

- Average latency: 6.36 ms
- Minimum latency: 0.05 ms
- Maximum latency: 17.83 ms

The benchmark report in the PR reports:

- Average latency: 9.88 ms
- Minimum latency: 0.56 ms
- Maximum latency: 27.66 ms

This is an internal inconsistency in the submitted benchmark evidence and should be reconciled.

### 5. Chatbot API Contract Test

Started the application successfully using Uvicorn.

A request using an invalid internal token was rejected with an unauthorized response.

A valid request using the documented development token returned a successful response containing:

- `reply`
- `conversation_id`
- `intent`
- `tokens_used`
- `source`

The response structure matched the documented chatbot contract.

### 6. Request Validation Tests

The following validation checks were performed:

- Missing `message` ? rejected
- Missing `user_id` ? rejected
- Missing `conversation_id` ? rejected
- Empty `message` ? rejected due to minimum length
- Missing `history` ? accepted as optional

Additional observation:

- Empty `user_id` was accepted.
- Empty `conversation_id` was accepted.

These are observations rather than confirmed contract violations because the current schema does not specify a minimum length for these fields.

### 7. Categorization Regression Test

Tested:

`POST /api/v1/categorize`

with a valid grocery expense.

Response included the expected contract fields:

- `category`
- `confidence`
- `alternative_categories`
- `needs_confirmation`
- `method`

The response matched the documented categorization contract.

### 8. Response Consistency Evidence

The submitted consistency evidence reports:

- Total executions: 15
- Passed: 12
- Flagged: 3
- Pass rate: 80%

TC-05 was flagged in all three cycles because of invalid/inconsistent output conditions.

This should be investigated before treating the benchmark as a clean quality baseline.

## Findings

### Blocker / Change Required

**1. Benchmark evidence contains inconsistent latency measurements.**

The PR description/log and benchmark report contain different latency values. The author should regenerate or reconcile the evidence and clearly identify the exact execution used for the reported numbers.

**2. Benchmark coverage is very small.**

Only 3 benchmark messages are used for latency/JSON evaluation. This is useful as a smoke test but is too small to support a strong performance baseline.

**3. Benchmark bypasses the HTTP API layer.**

`tests/ai_metrics_benchmark.py` directly calls `handle_chat()` instead of sending requests through `/api/v1/chatbot`.

Therefore, the benchmark measures service-level execution rather than the complete API path including HTTP routing, authentication, request validation, and response serialization.

**4. Response consistency is only 80%.**

TC-05 produced flagged/invalid responses in all three cycles. This should be investigated and either fixed or clearly documented as a known limitation.

### Minor Observations

- Direct execution of the benchmark script fails because of the `src` import path.
- Running it as a Python module succeeds.
- Empty `user_id` and `conversation_id` are currently accepted by the API schema.

## Evidence Screenshots

- [Benchmark Run 1](evidence/pr-93/01-benchmark-run-1.png)
- [Benchmark Run 2](evidence/pr-93/02-benchmark-run-2.png)
- [Server Startup](evidence/pr-93/03-server-startup.png)
- [Unauthorized Request](evidence/pr-93/04-unauthorized-request.png)
- [Valid Chatbot Response](evidence/pr-93/05-chatbot-valid-response.png)
- [Validation / Categorization Test](evidence/pr-93/06-validation-categorization.png)

## Final QA Assessment

**REQUEST CHANGES**

The core chatbot API contract and categorization response structure passed the independent API checks. However, PR #93 should be updated before approval because the submitted benchmark evidence is internally inconsistent, the benchmark coverage is very limited, the benchmark bypasses the actual HTTP API layer, and the consistency test contains repeated TC-05 failures.

After the author addresses these issues and regenerates the evidence, the PR can be re-tested.
