# Cross-Service Exception Boundary — Failure Injection Report

**Assignee:** Zainab Raza  
**Responsibility:** End-to-End Data Flow & Exception Handling  
**Branch:** `feature/task27-workflow-zainab`

## Objective

Harden the application-to-AI service boundary so downstream failures are
contained and returned as standard error payloads instead of crashing the
parent workflow.

## Implementation

**Module:**

```text
src/integration/cross_service_error_boundary.py
```

The module handles:

- request validation
- service-to-service authentication
- API timeouts
- network failures
- HTTP 429 rate limits
- authentication failures
- downstream 5xx failures
- model execution failures
- malformed AI responses
- stable error payloads containing `error_code`, `message`, and `request_id`

## Standard Error Payload

```json
{
  "error_code": "AI_TIMEOUT",
  "message": "AI assistant is temporarily unavailable.",
  "request_id": "req-001"
}
```

## Failure Injection Matrix

| Scenario | Injection | Expected Result |
|---|---|---|
| Successful request | HTTP 200 | Normal AI data returned |
| Timeout | `httpx.ReadTimeout` | `AI_TIMEOUT` |
| Rate limit | HTTP 429 | `AI_RATE_LIMITED` |
| Empty payload | `{}` | `EMPTY_PAYLOAD` |
| Unexpected input type | list instead of object | `INVALID_INPUT_TYPE` |
| Authentication failure | HTTP 401 | `AUTHENTICATION_ERROR` |
| Model execution failure | `ModelExecutionError` | `AI_MODEL_EXECUTION_ERROR` |
| Unexpected model exception | `RuntimeError` | `INTERNAL_ERROR` |
| Invalid JSON | malformed response | `INVALID_AI_RESPONSE` |
| Invalid response shape | JSON array | `INVALID_AI_RESPONSE` |
| Connection failure | `httpx.ConnectError` | `AI_SERVICE_UNAVAILABLE` |

## Parent-System Protection

```text
Parent Application
       |
       v
Cross-Service Error Boundary
       |
       v
AI Service / Model
       |
     failure
       |
       v
Failure is caught
       |
       v
Standard error payload
       |
       v
Parent workflow receives controlled result
```

Raw downstream exceptions are not allowed to escape the boundary for the
handled failure cases above.

## Automated Test Module

```text
tests/integration/test_cross_service_error_boundary.py
```

The test suite uses mocked HTTP responses and injected model failures. It does
not require a live AI service or provider credentials.

## Execution

Run:

```powershell
python -m pytest tests/integration/test_cross_service_error_boundary.py -v
```

Save the real output:

```powershell
python -m pytest tests/integration/test_cross_service_error_boundary.py -v | Tee-Object -FilePath .\docs\cross_service_error_boundary_execution.log
```

## Execution Result

**Pending local execution.**

The final test count and output must be copied from the actual local pytest
run. The execution log should contain that real output.

## Scope

This task covers cross-service exception containment and standard fallback
responses. It does not modify or duplicate the underlying AI/ML model logic.

## Completion Checklist

- [x] Cross-service error boundary implemented
- [x] Timeout handling implemented
- [x] Rate-limit handling implemented
- [x] Empty payload handling implemented
- [x] Unexpected input type handling implemented
- [x] Authentication failure handling implemented
- [x] Model execution failure handling implemented
- [x] Invalid AI response handling implemented
- [x] Failure injection tests implemented
- [ ] Tests executed locally
- [ ] Execution log generated from actual test execution
- [ ] `git diff --check` passed
- [ ] Changes committed on `feature/task27-workflow-zainab`
- [ ] Branch pushed to GitHub
- [ ] Pull Request opened

## GitHub Deliverable

Required branch:

```text
feature/task27-workflow-zainab
```

PR target:

```text
feature/task27-workflow-zainab → main
```

PR link:

```text
<Add PR URL after creating the pull request>
```
