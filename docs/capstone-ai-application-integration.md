# Capstone AI Application Integration

## 1. Objective

The objective is to connect the ready HisabDo AI service outputs with the Capstone application flow from the application side.

This work focuses on:

- consuming the existing AI service APIs
- mapping application requests to AI-service requests
- validating and normalizing AI-service responses
- identifying frontend and backend touchpoints
- documenting a sample end-to-end flow
- documenting authentication, errors, and remaining blockers

This task does **not** implement or duplicate AI model training, LLM logic, RAG implementation, or expense-model development.

---

## 2. Ready AI Services

The current AI service exposes two relevant application-facing capabilities.

### 2.1 Financial Assistant / Chatbot

**Endpoint**

```text
POST /api/v1/chatbot
```

The endpoint accepts:

- `user_id`
- `message`
- `conversation_id`
- optional `history`

The endpoint returns a `ChatbotResponse` containing:

- `reply`
- `conversation_id`
- optional `intent`
- optional `tokens_used`
- `source`

Possible `source` values currently documented in the service are:

- `rag`
- `backend_financial_api`
- `llm_general`

### 2.2 Smart Expense Categorization

**Endpoint**

```text
POST /api/v1/categorize
```

The endpoint accepts:

- optional `expense_id`
- `description`
- `amount`
- optional `merchant`
- `currency`

The endpoint returns:

- `category`
- `confidence`
- `alternative_categories`
- `needs_confirmation`
- `method`

The existing AI service also exposes:

```text
POST /api/v1/categorize/batch
```

for batch categorization.

---

## 3. Chatbot Request / Response Contract

### 3.1 Request Contract

The application should send the following structure to the AI service:

```json
{
  "user_id": "user-001",
  "message": "How much did I spend this month?",
  "conversation_id": "conv-001",
  "history": []
}
```

### 3.2 Request Fields

| Field | Type | Required | Purpose |
|---|---|---:|---|
| `user_id` | string | Yes | Identifies the application user |
| `message` | string | Yes | User's question/request |
| `conversation_id` | string | Yes | Identifies the conversation |
| `history` | array of objects | No | Previous conversation messages |

The `message` must be non-empty.

### 3.3 Response Contract

Example:

```json
{
  "reply": "Your expenses this month are 18,420 PKR.",
  "conversation_id": "conv-001",
  "intent": "own_financial_data",
  "tokens_used": 150,
  "source": "backend_financial_api"
}
```

### 3.4 Response Handling

The application should use:

- `reply` as the user-facing answer
- `conversation_id` to preserve conversation context
- `intent` for application logic or analytics when needed
- `tokens_used` as optional internal metadata
- `source` as optional transparency/debug metadata

The AI service currently routes questions about the user's own financial figures to backend financial data rather than RAG.

---

## 4. Expense Categorization Request / Response Contract

### 4.1 Request Contract

Example:

```json
{
  "expense_id": "exp-001",
  "description": "Bought groceries",
  "amount": 2500,
  "merchant": "Carrefour",
  "currency": "PKR"
}
```

### 4.2 Request Fields

| Field | Type | Required | Purpose |
|---|---|---:|---|
| `expense_id` | string | No | Application expense identifier |
| `description` | string | Yes | Text describing the expense |
| `amount` | number | Yes | Expense amount |
| `merchant` | string | No | Merchant information |
| `currency` | string | No | Currency; service currently defaults to `PKR` |

### 4.3 Response Contract

Example:

```json
{
  "category": "Shopping",
  "confidence": 0.94,
  "alternative_categories": [],
  "needs_confirmation": false,
  "method": "ml_model"
}
```

### 4.4 Response Handling

The application should:

1. use `category` as the predicted category
2. use `confidence` when displaying or applying confidence rules
3. use `alternative_categories` when alternatives are needed
4. use `needs_confirmation` to determine whether the user should confirm the prediction
5. treat `method` as optional diagnostic/trace information unless product requirements say otherwise

---

## 5. Frontend Touchpoints

### 5.1 Financial Assistant

Proposed frontend flow:

```text
AI Assistant screen
        ↓
Chat input
        ↓
Send button
        ↓
Application backend API
        ↓
Loading state
        ↓
Display `reply`
        ↓
Preserve `conversation_id`
```

Frontend responsibilities:

- collect the user's message
- send the request to the Capstone backend
- show a loading state
- display the returned assistant reply
- preserve conversation context where required
- handle application-level errors
- never expose AI-service credentials

### 5.2 Expense Categorization

Proposed frontend flow:

```text
Create / Edit Expense
        ↓
Expense description + amount + merchant
        ↓
Application backend
        ↓
AI categorization
        ↓
Predicted category
        ↓
Display / confirm category
```

Frontend responsibilities:

- collect transaction information
- submit the expense to the application backend
- display the predicted category
- display a confirmation UI when `needs_confirmation = true`
- handle unavailable-service or validation errors

### Status of Frontend Touchpoints

The current repository primarily contains the AI service and integration work; the final Capstone frontend screens and UI component names are not confirmed in this repository.

Therefore the frontend touchpoints above are **application integration mappings / proposed touchpoints** until the Capstone frontend team confirms the exact components.

---

## 6. Backend Touchpoints

### 6.1 Financial Assistant

```text
Capstone Backend
        ↓
Authenticate user
        ↓
Validate request
        ↓
Application AI client
        ↓
POST /api/v1/chatbot
        ↓
Validate AI response
        ↓
Return application-compatible response
```

Backend responsibilities:

- authenticate and authorize the user
- validate request data
- construct the AI-service request
- call the AI service
- pass the internal authentication header
- validate the AI response
- map service errors into application-level errors
- return only the fields required by the Capstone application

### 6.2 Expense Categorization

```text
Capstone Backend
        ↓
Validate transaction
        ↓
Application AI client
        ↓
POST /api/v1/categorize
        ↓
Receive prediction
        ↓
Apply application rules
        ↓
Return result to frontend
```

The backend should remain responsible for transaction persistence and business logic. The AI service only performs the AI categorization step.

---

## 7. End-to-End Flow

### 7.1 Financial Assistant Example

User asks:

```text
How much did I spend this month?
```

Flow:

```text
1. User enters the question
        ↓
2. Frontend sends request to Capstone backend
        ↓
3. Backend authenticates the user
        ↓
4. Backend validates the request
        ↓
5. Application AI client sends POST /api/v1/chatbot
        ↓
6. AI service processes the request
        ↓
7. AI service returns ChatbotResponse
        ↓
8. Application AI client validates / normalizes the response
        ↓
9. Backend returns an application-compatible response
        ↓
10. Frontend displays the assistant reply
```

Example AI-service response:

```json
{
  "reply": "Your expenses this month are 18,420 PKR.",
  "conversation_id": "conv-001",
  "intent": "own_financial_data",
  "source": "backend_financial_api"
}
```

### 7.2 Expense Categorization Example

User enters:

```text
Description: Bought groceries
Amount: 2500
Merchant: Carrefour
Currency: PKR
```

Flow:

```text
1. User creates an expense
        ↓
2. Frontend sends transaction to Capstone backend
        ↓
3. Backend validates the transaction
        ↓
4. Application AI client sends POST /api/v1/categorize
        ↓
5. AI service predicts the category
        ↓
6. AI service returns category/confidence information
        ↓
7. Backend validates the result
        ↓
8. Backend applies application business rules
        ↓
9. Frontend displays the predicted category
```

---

## 8. Error Handling

### 8.1 Request Validation

Invalid application requests should be rejected before the AI request is made.

Examples:

```text
Empty chatbot message
Missing required chatbot field
Empty expense description
Invalid field type
```

### 8.2 Authentication / Authorization

The AI service protects the chatbot and categorization endpoints with an internal service token.

An invalid or missing token should result in an authentication failure.

### 8.3 AI Service Errors

Application-side integration should handle cases such as:

```text
AI service unavailable
AI service timeout
Endpoint not found
Authentication failure
Rate limiting
Invalid AI response
Unexpected server error
```

The application should expose a stable, user-safe error response instead of leaking internal AI-service details.

### Proposed Application Error Example

```json
{
  "status": "error",
  "error_code": "AI_SERVICE_UNAVAILABLE",
  "message": "The AI service is temporarily unavailable."
}
```

The exact application error vocabulary should be confirmed with the Capstone backend team.

---

## 9. Authentication

The AI service currently uses an internal header:

```text
X-Internal-Token
```

The server validates this against:

```text
INTERNAL_SERVICE_TOKEN
```

### Application-side requirement

The Capstone backend/integration client should send:

```http
X-Internal-Token: <server-side-token>
```

The token must:

- remain server-side
- come from environment/approved secret management
- never be exposed in frontend code
- never be committed to GitHub

### Configuration Requirement

The following values need to be supplied through environment/configuration:

```text
AI_SERVICE_BASE_URL=<confirmed service URL>
INTERNAL_SERVICE_TOKEN=<approved secret>
```

The exact service URL and secret provisioning process are still integration dependencies.

---

## 10. Blockers

### Confirmed / Available

- Financial Assistant endpoint exists: `POST /api/v1/chatbot`
- Financial Assistant request/response schemas exist
- Expense Categorization endpoint exists: `POST /api/v1/categorize`
- Expense Categorization request/response schemas exist
- AI-service internal authentication mechanism is defined

### Remaining Integration Dependencies

1. **Capstone backend base URL**
   - The final application/backend endpoint that will call the AI service must be confirmed.

2. **AI service deployment URL**
   - The environment-specific AI service URL must be provided for live integration.

3. **Internal token provisioning**
   - The approved `INTERNAL_SERVICE_TOKEN` value and secret-management mechanism must be provided.

4. **Capstone frontend touchpoints**
   - Exact chatbot screen/components and expense UI components must be confirmed by the frontend team.

5. **Transaction persistence/business rules**
   - The backend must confirm when and how an AI-generated category is stored or presented for confirmation.

6. **Final application error contract**
   - The Capstone backend should confirm the final application-level error format and HTTP status mapping.

### Current Integration Status

```text
AI service contracts:              Available
Application-side mapping:         Defined
Frontend mapping:                 Proposed / needs confirmation
Backend mapping:                  Defined
Authentication mechanism:         Defined
Live Capstone integration:        Pending environment/contracts
```

---

## Scope Boundary

This task is limited to application-side integration.

It does not:

- train or retrain AI models
- implement the LLM
- implement RAG internals
- change the ML categorization pipeline
- duplicate AI-service business logic
- expose AI-service credentials to the frontend

The integration layer should consume the existing AI service as a downstream capability and provide a stable application-facing boundary.
