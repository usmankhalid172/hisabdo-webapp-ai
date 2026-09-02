# Cross-Service Error Boundary — Failure Injection Test Report

**Assignee:** Zainab Raza  
**Responsibility:** End-to-End Data Flow & Exception Handling  
**Branch:** `feature/task27-workflow-zainab`

## Objective

Harden the cross-service boundary so failures in downstream AI services are
returned as standard application errors instead of escaping and crashing the
parent workflow.

## Standard Error Contract

The boundary returns:

```json
{
  "error_code": "<machine-readable-code>",
  "message": "<safe-message>",
  "request_id": "<request-id>"
}
```

## Implementation

```text
src/integration/cross_service_fallback_handler.py
```

Responsibilities:

- validate payloads before transmission
- send service-to-service authentication
- contain API timeouts
- contain network failures
- map HTTP 429 rate limits
- map authentication failures
- contain downstream 5xx/model failures
- reject malformed AI responses
- preserve the parent request ID in error payloads

## Failure Injection Matrix

| Scenario | Injection | Expected result |
|---|---|---|
| Successful chatbot flow | HTTP 200 | AI response returned |
| Successful categorization flow | HTTP 200 | Category result returned |
| Missing payload | `{}` | `EMPTY_PAYLOAD` |
| Unexpected input type | list instead of object | `INVALID_INPUT_TYPE` |
| API timeout | `httpx.ReadTimeout` | `AI_TIMEOUT` |
| Rate limit | HTTP 429 | `AI_RATE_LIMITED` |
| Authentication failure | HTTP 401 | `AUTHENTICATION_ERROR` |
| Downstream/model failure | HTTP 500 | `AI_SERVICE_ERROR` |
| Invalid JSON | JSON decoding failure | `INVALID_AI_RESPONSE` |
| Invalid response shape | JSON array | `INVALID_AI_RESPONSE` |
| Connection failure | `httpx.ConnectError` | `AI_SERVICE_UNAVAILABLE` |
| Empty user message | blank string | `EMPTY_PAYLOAD` |

## Parent-System Protection

```text
Parent Application
        |
        v
Cross-Service Fallback Handler
        |
        v
AI Service / Model
        |
      failure
        |
        v
Failure captured
        |
        v
Standard error payload
        |
        v
Parent workflow receives controlled result
```

Handled downstream failures do not propagate as raw transport/model exceptions.

## Automated Test Module

```text
tests/integration/test_cross_service_fallback_handler.py
```

The tests use mocked HTTP responses and injected failures. No live AI
credentials are required.

## Execution

Run:

```powershell
python -m pytest tests/integration/test_cross_service_fallback_handler.py -v
```

Save the complete output:

```powershell
python -m pytest tests/integration/test_cross_service_fallback_handler.py -v | Tee-Object -FilePath .\docs\cross_service_fallback_execution.log
```

## Execution Result

**Pending local execution.**

The final test count must be copied from the actual local pytest output.

## Completion Checklist

- [x] Cross-service fallback handler implemented
- [x] Empty payload handling implemented
- [x] Unexpected input type handling implemented
- [x] API timeout handling implemented
- [x] Rate-limit handling implemented
- [x] Authentication failure handling implemented
- [x] Downstream/model failure handling implemented
- [x] Invalid AI response handling implemented
- [x] Connection failure handling implemented
- [x] Failure-injection tests implemented
- [ ] Tests executed locally
- [ ] Execution log generated from actual output
- [ ] Final `git diff --check` passed
- [ ] Changes committed
- [ ] Branch pushed
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
