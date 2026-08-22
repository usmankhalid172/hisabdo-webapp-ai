# Day 17 – Application AI Use-Case Mapping

**Project:** HisabDo Web App AI  
**Team:** Department 1 – Capstone Development / AI-ML Team  
**Repository:** `usmankhalid172/hisabdo-webapp-ai`  
**Document Path:** `docs/day-17-application-use-case-mapping.md`  
**Status:** Draft for Team Review

---

## 1. Objective

This document maps the AI capabilities identified in the HisabDo AI/ML workstream to their expected application-facing use cases.

The purpose is to clarify:

- the application purpose of each AI capability
- the expected trigger
- the data required by the AI capability
- the expected output
- the application component that consumes the result
- dependencies
- items that still require confirmation

This document distinguishes information confirmed by the repository from proposed application mappings and unresolved items.

---

## 2. Repository-Confirmed AI Capabilities

The current repository identifies these relevant AI/ML areas:

### 2.1 AI Financial Assistant / Chatbot

The repository describes this workstream as covering:

- LLM/NLP response flow
- RAG / knowledge-base support
- prompting and response validation
- financial question handling

### 2.2 Smart Expense Categorization

The repository describes this workstream as covering:

- expense text preprocessing
- feature preparation
- category prediction
- ML model training/inference
- model evaluation
- prediction service logic

### 2.3 AI Service / Application Integration

The repository describes this workstream as covering:

- FastAPI service layer
- request/response validation
- error handling and fallback behavior
- integration with the HisabDo application

These are repository-confirmed workstreams. The exact production application screens, endpoints, and user workflows are not fully specified in the current repository documentation and are therefore marked as TBD below.

---

## 3. Use-Case Classification

The following classifications are used throughout this document.

### Confirmed

Directly supported by current repository/workspace documentation.

### Proposed

A logical application-facing mapping derived from the confirmed AI workstream.

### TBD / Requires Confirmation

A product, frontend, backend, or AI/ML decision that is not confirmed by the available project documentation.

---

# 4. Application AI Use-Case Matrix

| AI Capability / Use Case | Application Purpose | Trigger | Input Data | AI Capability / Service | Expected Output | Application Consumer | Dependencies | Status |
|---|---|---|---|---|---|---|---|---|
| Financial Assistant / Financial Q&A | Allow the application to obtain AI-generated answers to financial questions | User submits a financial question | User question and any application context approved by the backend | Financial Assistant / LLM; RAG where required | AI-generated answer; optional supporting source/context information | Backend → Frontend | AI service, application API, approved financial context, optional RAG | Confirmed workstream; application mapping proposed |
| Smart Expense Categorization | Automatically assign a category to a transaction | Transaction is created/imported or categorization is requested | Transaction fields required by the model/service | Expense categorization model/service | Predicted category; confidence if supported | Backend and/or transaction UI | Transaction data model, prediction service, agreed category set | Confirmed workstream; exact trigger/fields TBD |
| Financial Knowledge / RAG Support | Provide retrieved knowledge to support an AI answer where retrieval is required | Financial question requires knowledge retrieval | User question plus retrieval context | RAG / knowledge-base component | Retrieved context and/or sources used by the assistant | AI service / Backend | Knowledge base, retrieval service, source data | Repository-confirmed capability; exact application usage TBD |

---

# 5. Financial Assistant Use-Case Mapping

## 5.1 Purpose

### Confirmed

The repository identifies a Financial Assistant / Chatbot workstream for financial question handling, LLM/NLP response flow, prompting/response validation, and RAG/knowledge-base support.

### Proposed application mapping

```text
User
  ↓
Application UI
  ↓
Application Backend
  ↓
AI Integration Layer
  ↓
Financial Assistant / RAG / LLM
  ↓
AI Response
  ↓
Application Backend
  ↓
Application UI
```

The exact UI location is **TBD** because the current repository documentation does not specify a final production screen.

## 5.2 Trigger

### Proposed

A user submits a financial question/request through an application-facing assistant interface.

Example:

```text
How much did I spend on food?
```

The exact supported question set and user interaction flow require product/frontend confirmation.

## 5.3 Input Data

### Proposed

At minimum, the AI request is expected to contain the user's question/message.

Additional application context may be provided only when required and approved by the backend/AI team.

Potential context may include:

- conversation/session identifier
- authenticated application user context
- relevant financial context
- currency/language context

The exact available fields are **TBD** and must follow the confirmed backend/API contract.

## 5.4 Expected Output

### Proposed

The application-facing result should contain:

- processing status
- AI-generated response
- request identifier where supported
- optional sources/metadata where RAG is used

The exact response contract should remain aligned with the Day 16 integration component and final AI-service contract.

## 5.5 Consumer

### Proposed

```text
AI Service
    ↓
AI Integration Layer
    ↓
HisabDo Backend
    ↓
Frontend
```

The frontend is expected to consume the application-level response rather than a provider-specific response format.

---

# 6. Smart Expense Categorization Use-Case Mapping

## 6.1 Purpose

### Confirmed

The repository identifies Smart Expense Categorization as a dedicated workstream covering preprocessing, feature preparation, category prediction, model training/inference, model evaluation, and prediction service logic.

### Proposed application mapping

```text
Transaction
   ↓
HisabDo Backend
   ↓
AI Integration Layer / Prediction Service
   ↓
Expense Categorization Model
   ↓
Predicted Category
   ↓
HisabDo Backend
   ↓
Transaction / Application Workflow
```

The exact application screen or workflow is **TBD**.

## 6.2 Trigger

### Proposed

Categorization is triggered when a transaction requires a category prediction.

Possible triggers include:

- transaction creation
- transaction import
- explicit recategorization request

The final trigger must be confirmed by the backend/product team.

## 6.3 Input Data

### Confirmed

The repository states that model inputs should be documented once the team confirms the final model contract.

### Proposed

Candidate transaction information may include:

- transaction description
- amount
- currency
- transaction identifier

These fields are examples for integration planning and are not confirmed as the final model input contract.

## 6.4 Expected Output

### Proposed

The application-facing result may contain:

- predicted category
- confidence score when the model/service provides one
- processing status

The final category vocabulary and output fields require AI/ML and backend confirmation.

## 6.5 Consumer

### Proposed

```text
Prediction Service
     ↓
AI Integration Layer
     ↓
Backend
     ↓
Transaction/Application Workflow
```

Whether the frontend displays the prediction directly or the backend stores/uses it automatically requires confirmation.

---

# 7. RAG / Knowledge Support Mapping

## 7.1 Purpose

### Confirmed

RAG / knowledge-base support is explicitly identified within the Financial Assistant workstream.

## 7.2 Proposed flow

```text
User Question
      ↓
AI Integration Layer
      ↓
Retrieval / Knowledge Base
      ↓
Relevant Context
      ↓
Financial Assistant / LLM
      ↓
Validated Response
      ↓
Application
```

## 7.3 Input

### Proposed

- user question
- retrieval query/context
- approved knowledge-base data

## 7.4 Output

### Proposed

- retrieved context
- source references where available
- final AI response using the retrieved information

## 7.5 Open Questions

- Is RAG required for all Financial Assistant questions or only selected categories?
- Which knowledge sources are authoritative?
- Should source references be displayed to users?
- What retrieval service/store will be used?
- Who owns updates to the knowledge base?

These decisions require AI/ML and product/team confirmation.

---

# 8. Frontend Mapping

The frontend responsibilities below are **proposed application-facing responsibilities**, not claims that the final UI is already implemented.

| Use Case | Proposed Frontend Responsibility |
|---|---|
| Financial Assistant | Collect user question, send application request, display loading state, render validated response, show fallback/error state |
| Expense Categorization | Display predicted category where the product requires it, allow any approved correction workflow, show error/fallback state if applicable |
| RAG-supported response | Render the assistant response and source information if the product decides to expose sources |

### Frontend items requiring confirmation

1. Final location of the Financial Assistant in the UI
2. Whether AI responses are streamed or returned as complete responses
3. Which response metadata should be displayed
4. Whether confidence scores are shown to users
5. User-facing fallback/error messages
6. Whether users can correct AI-generated categories

---

# 9. Backend Mapping

The backend is expected to provide the application-facing boundary for AI service consumption.

### Proposed responsibilities

```text
Authentication
     ↓
Authorization
     ↓
Request validation
     ↓
AI integration/client
     ↓
AI response validation
     ↓
Application-level response
```

### Backend dependencies

- application authentication/session context
- transaction data where required
- application API contract
- AI integration component
- AI service endpoint
- approved error-handling behavior

### Backend items requiring confirmation

1. Exact transaction fields available to the AI service
2. Final user/context fields permitted in AI requests
3. Final AI service endpoint and authentication
4. Whether AI output is persisted
5. Synchronous vs asynchronous processing for each use case
6. Retry and timeout policy

---

# 10. End-to-End Application AI Flow

## Proposed

```text
User
  ↓
HisabDo Frontend
  ↓
HisabDo Backend
  ↓
AI Integration Layer
  ├── Financial Assistant
  │      └── RAG / Knowledge Base when required
  │
  └── Expense Categorization
  ↓
Validated / Normalized AI Response
  ↓
HisabDo Backend
  ↓
HisabDo Frontend / Application Workflow
```

---

# 11. Use-Case-to-Component Mapping

| Application Need | AI/ML Component | Integration Responsibility | Application Consumer |
|---|---|---|---|
| Answer financial questions | Financial Assistant / LLM | Request routing, validation, response normalization | Backend → Frontend |
| Retrieve supporting financial knowledge | RAG / Knowledge Base | Retrieval orchestration and response handling | Financial Assistant / Backend |
| Categorize expenses | Expense Categorization Service / Model | Request formatting, validation, response handling | Backend / Transaction workflow |

---

# 12. Dependencies

| Dependency | Purpose | Responsible Area | Status |
|---|---|---|---|
| HisabDo Backend | Application API, authentication and orchestration | Backend | Existing application dependency |
| HisabDo Frontend | User interaction and response presentation | Frontend | Existing application dependency |
| AI Integration Layer | Application-facing AI communication | AI/ML / Backend | Day 16 component prepared |
| Financial Assistant | Financial question handling | AI/ML | Confirmed workstream |
| Expense Categorization | Transaction category prediction | AI/ML | Confirmed workstream |
| RAG / Knowledge Base | Retrieval support for Financial Assistant | AI/ML | Confirmed capability; final integration TBD |
| AI/LLM service endpoint | AI processing | AI/ML | Final endpoint TBD |
| Transaction data model | Inputs for categorization | Backend | Final fields TBD |
| Approved knowledge sources | RAG context | AI/ML / Product | TBD |

---

# 13. Confirmed vs Proposed vs TBD

## Confirmed

- Financial Assistant / Chatbot is an identified AI/ML workstream.
- Smart Expense Categorization is an identified AI/ML workstream.
- RAG / knowledge-base support is part of the Financial Assistant workstream.
- AI Service / Application Integration is an identified workstream.
- The integration area is responsible for application-facing API integration, validation, error handling and orchestration.

## Proposed

- Financial Assistant is consumed through an application-facing backend/integration layer.
- Expense Categorization is invoked when a transaction requires categorization.
- RAG is invoked when a Financial Assistant request requires knowledge retrieval.
- AI responses are validated and normalized before reaching application consumers.
- The frontend consumes application-level responses rather than provider-specific responses.

## TBD / Requires Confirmation

- Final Financial Assistant UI location
- Final product-approved AI use cases
- Exact request fields available from the backend
- Exact expense-category vocabulary
- Final AI-service endpoint and authentication
- RAG invocation rules
- Authoritative knowledge sources
- Whether confidence scores are displayed
- Whether AI outputs are persisted
- Streaming requirements
- Final timeout/retry behavior

---

# 14. Open Questions

1. Which AI use cases are officially part of the current application MVP?
2. Where should the Financial Assistant appear in the final application?
3. Which financial data is the assistant permitted to access?
4. Which transaction fields are available for expense categorization?
5. What are the final accepted expense categories?
6. When should RAG be invoked?
7. Which knowledge sources are authoritative?
8. Should AI-generated sources/references be displayed to users?
9. Should category confidence be displayed?
10. Should AI-generated results be stored in the application?
11. Which AI operations must support synchronous responses?
12. What should the user see when the AI service is unavailable?

---

# 15. Blockers / Risks

### Current blockers

- Final application use-case decisions require confirmation from product/frontend/backend/AI stakeholders.
- Final AI-service endpoint and authentication remain dependent on the AI/ML integration contract.
- Final transaction input/output fields require backend and AI/ML confirmation.
- Final RAG usage and authoritative knowledge sources require confirmation.

### Integration risks

- AI output may not match the application's expected schema.
- AI service availability/latency may affect user experience.
- Sending unnecessary financial/user data to AI services creates avoidable privacy and security risk.
- Changes to the AI contract can affect frontend/backend consumers.

---

# 16. Recommended Application Mapping

The following mapping is recommended for further team discussion.

| Priority | Use Case | Recommendation |
|---|---|---|
| High | Financial Assistant / Financial Q&A | Use as the primary conversational AI capability |
| High | Smart Expense Categorization | Use in the transaction categorization workflow |
| Medium | RAG / Knowledge Support | Use to support Financial Assistant responses where retrieval is required |

These priorities are recommendations only and are not confirmed product decisions.

---

# 17. Day 17 Evidence

### Work Product

```text
docs/day-17-application-use-case-mapping.md
```

### GitHub

```text
Branch:
feature/zainab-raza-application-use-case-mapping-day-17

Commit:
<TBD after commit>

Pull Request:
<TBD after PR creation>
```

### Validation

The document should be reviewed against the Day 17 responsibility for:

- AI use-case identification
- application mapping
- input/output mapping
- frontend/backend responsibility mapping
- dependencies
- open questions
- blocker tracking

### Remaining Work

- Confirm final product-approved use cases.
- Confirm application locations/workflows.
- Confirm final data contracts.
- Resolve AI/ML and backend dependencies.
