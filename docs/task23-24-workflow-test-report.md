# Task 23–24 — End-to-End Workflow Data Flow Test Report

**Responsibility:** End-to-End Data Flow Testing  
**Branch:** `feature/task23-24-workflow-zainab`  
**Repository:** `usmankhalid172/hisabdo-webapp-ai`

---

## 1. Objective

The objective of this task is to test data transmission between the application/backend workflow and the existing HisabDo AI service.

The testing focuses on:

- successful application-to-AI data transmission
- API timeout handling
- empty payload handling
- unexpected input type handling
- authentication failure handling
- invalid or unexpected AI responses
- predictable error and fallback behavior

This task validates the **application-to-AI integration boundary** and does not duplicate AI model training, LLM implementation, RAG implementation, or AI-service business logic.

---

## 2. Workflow Under Test

The tested workflow is:

```text
Application / Backend
        |
        v
AIWorkflowClient
        |
        | HTTP + JSON
        | X-Internal-Token
        v
HisabDo AI Service
        |
        +----------------------+
        |                      |
        v                      v
POST /api/v1/chatbot     POST /api/v1/categorize
        |                      |
        +----------+-----------+
                   |
                   v
              AI Response
                   |
                   v
             AIWorkflowClient
                   |
                   v
          Application / Backend
```

The workflow client acts only as the application-side transport and validation boundary. AI processing remains inside the existing AI service.

---

## 3. Workflow Module

**File:**

```text
src/integration/workflow_client.py
```

### Responsibilities

The workflow module is responsible for:

- validating request input before transmission
- constructing JSON request payloads
- sending requests to the existing AI service
- adding the internal service authentication header
- handling network failures and timeouts
- mapping common HTTP errors to predictable application errors
- validating that successful AI responses have an expected object structure

### Supported AI endpoints

```text
POST /api/v1/chatbot
POST /api/v1/categorize
```

---

## 4. Automated Test Module

**File:**

```text
tests/integration/test_workflow_client.py
```

The automated tests use mocked HTTP responses. No live AI provider, API key, or deployed AI-service environment is required for these tests.

The test suite verifies both successful data transmission and failure handling.

### Test scenarios

| # | Test Scenario | Expected Result |
|---|---|---|
| 1 | Valid chatbot request | Request is transmitted and AI response is returned |
| 2 | Valid expense categorization request | Request is transmitted and category response is returned |
| 3 | Empty payload | Request is rejected before network transmission |
| 4 | Unexpected input type | Request is rejected with input-type error |
| 5 | API timeout | Timeout is converted to `AI_TIMEOUT` / HTTP 504 |
| 6 | Authentication failure | 401/403 response is mapped to authentication error |
| 7 | Invalid JSON response | Response is rejected as invalid AI response |
| 8 | Unexpected response structure | Response is rejected as invalid AI response |

---

## 5. Error and Fallback Behavior

### 5.1 API Timeout

```text
AI service request
       |
       v
HTTP timeout
       |
       v
WorkflowTimeoutError
       |
       v
error_code = AI_TIMEOUT
       |
       v
HTTP 504
```

The low-level timeout exception is converted into a predictable workflow error.

### 5.2 Empty Payload

```text
Empty request
       |
       v
EmptyPayloadError
       |
       v
error_code = EMPTY_PAYLOAD
       |
       v
HTTP 400
```

The request is rejected before any network call is made.

### 5.3 Unexpected Input Type

```text
Unexpected input type
       |
       v
InvalidInputTypeError
       |
       v
error_code = INVALID_INPUT_TYPE
       |
       v
HTTP 400
```

The request is rejected before it reaches the AI service.

### 5.4 Authentication Failure

```text
AI service
    |
    | 401 / 403
    v
WorkflowServiceError
    |
    v
error_code = AUTHENTICATION_ERROR
```

The application does not expose the internal authentication details to the user.

### 5.5 Invalid AI Response

```text
Invalid JSON /
unexpected response structure
          |
          v
WorkflowResponseError
          |
          v
error_code = INVALID_AI_RESPONSE
          |
          v
HTTP 502
```

This prevents malformed downstream responses from being silently accepted by the application.

---

## 6. Chatbot Data Flow

### Sample request

```json
{
  "user_id": "user-001",
  "message": "What is my balance?",
  "conversation_id": "conv-001",
  "history": []
}
```

### Downstream endpoint

```text
POST /api/v1/chatbot
```

### Sample response

```json
{
  "reply": "Your balance is 45,230.50 PKR.",
  "conversation_id": "conv-001",
  "intent": "own_financial_data",
  "tokens_used": 120,
  "source": "backend_financial_api"
}
```

### Expected flow

```text
Frontend / Application
        |
        v
Capstone Backend
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
AIWorkflowClient
        |
        v
Capstone Backend
        |
        v
Frontend
```

---

## 7. Expense Categorization Data Flow

### Sample request

```json
{
  "expense_id": "exp-001",
  "description": "Bought groceries",
  "amount": 2500,
  "merchant": "Carrefour",
  "currency": "PKR"
}
```

### Downstream endpoint

```text
POST /api/v1/categorize
```

### Sample response

```json
{
  "category": "Shopping",
  "confidence": 0.94,
  "alternative_categories": [
    "Groceries"
  ],
  "needs_confirmation": false,
  "method": "ml_model"
}
```

### Expected flow

```text
Frontend / Application
        |
        v
Capstone Backend
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
AIWorkflowClient
        |
        v
Capstone Backend
        |
        v
Frontend
```

---

## 8. Authentication

The workflow client sends service-to-service authentication using:

```http
X-Internal-Token: <server-side-token>
```

The token is expected to remain on the server side.

### Configuration

The client reads:

```text
AI_SERVICE_BASE_URL=<AI service URL>
AI_SERVICE_INTERNAL_TOKEN=<internal service token>
AI_SERVICE_TIMEOUT_SECONDS=15
```

### Security requirements

The internal token must:

- remain on trusted server-side components
- be provided through environment/configuration
- never be committed to Git
- never be exposed in frontend code
- never be logged as plaintext

---

## 9. Execution Command

Run the integration test suite from the repository root:

```powershell
python -m pytest tests/integration/test_workflow_client.py -v
```

The execution log is also saved with:

```powershell
python -m pytest tests/integration/test_workflow_client.py -v | Tee-Object -FilePath .\docs	ask23-24-workflow-execution.log
```

---

## 10. Execution Result

The workflow integration test suite was executed locally.

### Result

```text
8 passed in 0.25s
```

### Covered scenarios

All 8 tests passed for:

- chatbot data transmission
- expense categorization data transmission
- empty payload handling
- unexpected input type handling
- timeout handling
- authentication failure handling
- invalid JSON response handling
- unexpected response structure handling

### Execution log

The complete command output is stored in:

```text
docs/task23-24-workflow-execution.log
```

### Warning

During execution, `pytest-asyncio` produced a `PytestDeprecationWarning` related to the unspecified `asyncio_default_fixture_loop_scope` configuration.

This warning did not cause any test failure.

---

## 11. Test Evidence Summary

| Area | Result |
|---|---|
| Chatbot data transmission | PASS |
| Expense categorization transmission | PASS |
| Empty payload validation | PASS |
| Unexpected input type validation | PASS |
| API timeout handling | PASS |
| Authentication error handling | PASS |
| Invalid JSON handling | PASS |
| Unexpected response structure handling | PASS |
| Overall automated test result | **8 passed** |

---

## 12. Blockers / Dependencies

The automated workflow tests can run without a live AI-service deployment because HTTP calls are mocked.

For real end-to-end environment testing, the following are required:

1. **AI service deployment URL**

   A reachable environment-specific value is required for `AI_SERVICE_BASE_URL`.

2. **Internal service token**

   A valid `AI_SERVICE_INTERNAL_TOKEN` must be provided through the approved secret-management mechanism.

3. **Network connectivity**

   The application/backend environment must be able to reach the deployed AI service.

4. **Environment-level verification**

   Actual deployment/network behavior should be verified separately from the mocked automated test suite.

---

## 13. Scope Boundary

This task is limited to workflow/data-flow testing at the application-to-AI boundary.

It does **not**:

- train or retrain AI models
- modify the Financial Assistant implementation
- modify the expense categorization model
- implement RAG
- change AI-service business logic
- expose provider credentials
- replace existing AI-service functionality

---

## 14. Completion Checklist

- [x] Workflow module implemented
- [x] Successful chatbot data flow tested
- [x] Successful expense categorization data flow tested
- [x] API timeout handling tested
- [x] Empty payload handling tested
- [x] Unexpected input type handling tested
- [x] Authentication failure handling tested
- [x] Invalid AI response handling tested
- [x] Execution log generated
- [x] Execution result recorded
- [ ] Final `git diff --check` completed
- [ ] Changes committed on `feature/task23-24-workflow-zainab`
- [ ] Branch pushed to GitHub
- [ ] Pull Request opened
- [ ] PR link added to this report

---

## 15. GitHub Deliverable

**Required branch:**

```text
feature/task23-24-workflow-zainab
```

**Required PR target:**

```text
feature/task23-24-workflow-zainab → main
```

### PR link

```text
<Add GitHub Pull Request URL after creating the PR>
```

---

## 16. Final Status

```text
Workflow module:                 COMPLETED
Automated workflow tests:        COMPLETED
Error handling tests:            COMPLETED
Execution log:                   COMPLETED
Test result:                     8 PASSED
Git commit:                      PENDING
GitHub push:                     PENDING
Pull Request:                    PENDING
```
