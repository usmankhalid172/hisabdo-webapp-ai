# Task 15–25 — End-to-End Workflow Data Flow Test Report

**Assignee:** Zainab Raza  
**Responsibility:** End-to-End Data Flow Testing  
**Branch:** `feature/task15-25-workflow-zainab`  
**Repository:** `usmankhalid172/hisabdo-webapp-ai`

---

## 1. Objective

Test data transmission between the application/backend workflow and the existing HisabDo AI components.

The workflow must also provide robust error handling and safe fallback behavior for:

- API timeouts
- empty payloads
- quota/rate-limit responses
- unexpected input types
- authentication failures
- unavailable services
- malformed AI responses

The implementation is limited to the application-to-AI integration boundary and does not duplicate AI/ML model or AI-service business logic.

---

## 2. Workflow Under Test

```text
Capstone Application / Backend
              |
              v
       AIWorkflowClient
              |
       HTTP + JSON +
       X-Internal-Token
              |
              v
       HisabDo AI Service
          /                   v            v
   /api/v1/chatbot   /api/v1/categorize
         \            /
          v          v
           AI Response
                |
                v
         AIWorkflowClient
                |
                v
       Application / Backend
```

---

## 3. Tested Workflow Module

**File:**

```text
src/integration/task15_25_workflow.py
```

The module:

- validates inputs before transmission
- sends JSON requests to existing AI endpoints
- adds service-to-service authentication
- maps timeout failures to `AI_TIMEOUT`
- maps quota/rate-limit failures to `AI_QUOTA_EXCEEDED`
- maps invalid input types to `INVALID_INPUT_TYPE`
- maps empty payloads to `EMPTY_PAYLOAD`
- maps authentication errors
- maps unavailable-service errors
- rejects malformed AI responses
- returns safe application-facing fallback messages

---

## 4. Automated Test Module

**File:**

```text
tests/integration/test_task15_25_workflow.py
```

The test suite uses mocked HTTP responses. No live AI credentials are required.

### Test scenarios

| # | Scenario | Expected result |
|---|---|---|
| 1 | Valid chatbot transmission | AI response returned |
| 2 | Valid expense categorization transmission | Category response returned |
| 3 | Empty chatbot message | `EMPTY_PAYLOAD` fallback |
| 4 | Empty expense description | `EMPTY_PAYLOAD` fallback |
| 5 | Unexpected input type | `INVALID_INPUT_TYPE` fallback |
| 6 | API timeout | `AI_TIMEOUT` fallback / HTTP 504 |
| 7 | Quota/rate limit | `AI_QUOTA_EXCEEDED` fallback / HTTP 429 |
| 8 | Authentication failure | `AUTHENTICATION_ERROR` |
| 9 | Invalid JSON response | `INVALID_AI_RESPONSE` / HTTP 502 |
| 10 | Unexpected response structure | `INVALID_AI_RESPONSE` / HTTP 502 |
| 11 | Network/connection failure | `AI_SERVICE_UNAVAILABLE` / HTTP 503 |

---

## 5. Data Transmission — Chatbot

### Request

```json
{
  "user_id": "user-001",
  "message": "What is my balance?",
  "conversation_id": "conv-001",
  "history": []
}
```

### Endpoint

```text
POST /api/v1/chatbot
```

### Expected response shape

```json
{
  "reply": "Your balance is 45,230.50 PKR.",
  "conversation_id": "conv-001",
  "intent": "own_financial_data",
  "source": "backend_financial_api"
}
```

### Flow

```text
Application
    |
    v
AIWorkflowClient.chatbot()
    |
    v
POST /api/v1/chatbot
    |
    v
AI Service
    |
    v
Chatbot response
    |
    v
Application
```

---

## 6. Data Transmission — Expense Categorization

### Request

```json
{
  "expense_id": "exp-001",
  "description": "Bought groceries",
  "amount": 2500,
  "merchant": "Carrefour",
  "currency": "PKR"
}
```

### Endpoint

```text
POST /api/v1/categorize
```

### Expected response shape

```json
{
  "category": "Shopping",
  "confidence": 0.94,
  "alternative_categories": [],
  "needs_confirmation": false,
  "method": "ml_model"
}
```

### Flow

```text
Application
    |
    v
AIWorkflowClient.categorize_expense()
    |
    v
POST /api/v1/categorize
    |
    v
AI Service
    |
    v
Category response
    |
    v
Application
```

---

## 7. Error and Fallback Logic

### API Timeout

```text
HTTP timeout
      |
      v
AI_TIMEOUT
      |
      v
Safe fallback message
      |
      v
HTTP 504
```

### Empty Payload

```text
Empty input
    |
    v
EMPTY_PAYLOAD
    |
    v
HTTP 400
    |
    v
No network request
```

### Unexpected Input Type

```text
Wrong type
    |
    v
INVALID_INPUT_TYPE
    |
    v
HTTP 400
    |
    v
No network request
```

### Quota / Rate Limit

```text
AI service returns 429
       |
       v
AI_QUOTA_EXCEEDED
       |
       v
Safe retry-later message
       |
       v
HTTP 429
```

### Authentication Failure

```text
401 / 403
    |
    v
AUTHENTICATION_ERROR
    |
    v
Safe application error
```

### Invalid AI Response

```text
Invalid JSON /
unexpected structure
        |
        v
INVALID_AI_RESPONSE
        |
        v
HTTP 502
```

### Network Failure

```text
Connection failure
       |
       v
AI_SERVICE_UNAVAILABLE
       |
       v
HTTP 503
```

---

## 8. Authentication

Service-to-service authentication uses:

```http
X-Internal-Token: <server-side-token>
```

Configuration expected by the workflow client:

```text
AI_SERVICE_BASE_URL=<AI service URL>
AI_SERVICE_INTERNAL_TOKEN=<internal service token>
AI_SERVICE_TIMEOUT_SECONDS=15
```

The internal token must remain server-side and must not be committed to Git or exposed to the frontend.

---

## 9. Execution Command

Run from the repository root:

```powershell
python -m pytest tests/integration/test_task15_25_workflow.py -v
```

To save the complete execution output:

```powershell
python -m pytest tests/integration/test_task15_25_workflow.py -v | Tee-Object -FilePath .\docs	ask15-25-workflow-execution.log
```

---

## 10. Execution Result

The workflow integration test suite was executed locally.

### Result

```text
11 passed in 0.11s
```

All 11 workflow integration tests passed successfully.

### Covered scenarios

- successful chatbot data transmission
- successful expense categorization data transmission
- empty chatbot message handling
- empty expense description handling
- unexpected input type handling
- API timeout handling
- quota/rate-limit handling
- authentication failure handling
- invalid JSON response handling
- unexpected response structure handling
- network/connection failure handling

### Execution log

The complete terminal output is stored in:

```text
docs/task15-25-workflow-execution.log
```

### Warning

During execution, `pytest-asyncio` produced a `PytestDeprecationWarning`
related to the unspecified `asyncio_default_fixture_loop_scope` configuration.

This warning did not cause any test failure.

---

## 11. Test Evidence Summary

| Area | Result |
|---|---|
| Chatbot data transmission | PASS |
| Expense categorization transmission | PASS |
| Empty chatbot message handling | PASS |
| Empty expense description handling | PASS |
| Unexpected input type handling | PASS |
| API timeout handling | PASS |
| Quota/rate-limit handling | PASS |
| Authentication failure handling | PASS |
| Invalid JSON handling | PASS |
| Unexpected response structure handling | PASS |
| Network/connection failure handling | PASS |
| Overall automated test result | **11 PASSED** |

---

## 12. Blockers / Dependencies

### Automated testing

The test suite uses mocked HTTP responses, so it does not require:

- a deployed AI service
- a live AI provider
- a production API key

### Required for real environment testing

- reachable AI service URL
- valid internal service token
- network connectivity between application/backend and AI service
- final environment configuration

These are environment dependencies and do not prevent the mocked workflow tests from running.

---

## 13. Scope Boundary

This task tests application-to-AI data transmission and fallback behavior.

It does not:

- train or retrain AI models
- modify the Financial Assistant implementation
- modify the expense categorization model
- implement RAG
- change AI-service business logic
- expose provider credentials

---

## 14. Completion Checklist

- [x] Workflow module implemented
- [x] Chatbot transmission test implemented
- [x] Expense categorization transmission test implemented
- [x] Empty payload handling implemented
- [x] Unexpected input type handling implemented
- [x] API timeout fallback implemented
- [x] Quota/rate-limit fallback implemented
- [x] Authentication failure handling implemented
- [x] Invalid response handling implemented
- [x] Network failure handling implemented
- [x] Automated tests executed
- [x] Execution log generated from actual test execution
- [x] Execution result recorded
- [ ] Final `git diff --check` passed
- [ ] Changes committed on `feature/task15-25-workflow-zainab`
- [ ] Branch pushed to GitHub
- [ ] Pull Request opened
- [ ] PR link added below

---

## 15. GitHub Deliverable

**Required branch:**

```text
feature/task15-25-workflow-zainab
```

**Pull Request target:**

```text
feature/task15-25-workflow-zainab → main
```

### PR Link

```text
<Add GitHub Pull Request URL after creating the PR>
```

---

## 16. Final Status

```text
Workflow module:              COMPLETED
Error/fallback logic:         COMPLETED
Automated tests:              COMPLETED
Execution log:                COMPLETED
Test result:                  11 PASSED
Git commit:                   PENDING
GitHub push:                  PENDING
Pull Request:                 PENDING
```
