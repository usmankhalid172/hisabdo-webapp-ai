# Day 18 — RAG/ML Integration Risks, Improvements & Technical Notes

**Project:** HisabDo Web App AI  
**Department:** Department 1 – Capstone Development  
**Track:** AI/ML  
**Workstream:** RAG/ML Integration Support  
**Intern:** Farheen Fatima  
**Task:** Document RAG/ML integration risks, practical improvement options and supporting technical notes  
**Day:** 18

---

## 1. Objective

The objective of this document is to review the planned integration of the Department 1 AI/ML components with the HisabDo application and identify practical technical risks, limitations, improvement options, coordination requirements, and open blockers.

The review continues the previous RAG/ML research and AI use-case improvement work without duplicating the primary implementation owned by other feature members.

The target application flow is:

**User → HisabDo App → Backend/API → AI Service → Model/LLM → Validated Response → User**

---

## 2. Current AI/ML Components Reviewed

Based on the current repository structure, the main AI/ML components are:

### 2.1 Financial Assistant / Chatbot

Location:

`src/financial_assistant/`

Current status:

- Financial Assistant module exists as a planned module.
- No production chatbot implementation is currently present in this module.
- Previous work defined financial question categories, expected behavior, prompt requirements, and test scenarios.
- Future implementation may use LLM/RAG-based question answering.

### 2.2 Smart Expense Categorization

Location:

`src/expense_categorization/`

Current implementation includes:

- TF-IDF text representation.
- Logistic Regression classifier.
- Training/test split based on unique descriptions.
- Accuracy, Precision, Recall and F1-score evaluation.
- Saved model pipeline using joblib.

Current dataset characteristics:

- 500 rows.
- 3 columns: `description`, `amount`, `category`.
- 10 expense categories.
- 50 records per category.
- 200 unique descriptions.

The current baseline was tested locally with:

- Accuracy: approximately 78.64%
- Weighted Precision: approximately 85.92%
- Weighted Recall: approximately 78.64%
- Weighted F1-score: approximately 79.03%

These results provide a useful baseline but should not yet be treated as production-level performance.

### 2.3 AI Service / Application Integration

Location:

`src/integration/`

Current status:

- Integration module exists as the intended location for FastAPI/service-layer functionality.
- Current module contains documentation only.
- No final application-facing AI API implementation is currently present in this module.

Therefore, integration recommendations in this document are intended to support future implementation rather than claim that the complete integration already exists.

---

## 3. Target Integration Flow

The recommended high-level flow is:

```text
User
  ↓
HisabDo Web Application
  ↓
Backend / API
  ↓
AI Service
  ↓
Request / Input Validation
  ↓
 ┌───────────────────────────────┐
 │                               │
 ↓                               ↓
Financial Assistant          Expense Categorization
 │                               │
 ↓                               ↓
Retriever / LLM              ML Model
 │                               │
 └───────────────┬───────────────┘
                 ↓
          Response Validation
                 ↓
          Backend / API Response
                 ↓
                User
```

The important design principle is that the LLM or ML model should not directly control application behavior without validation.

---

## 4. Integration Risks

### 4.1 Incorrect or Missing Retrieval

For the Financial Assistant, incorrect retrieval can result in an answer based on irrelevant financial records.

**Risk**

The chatbot may return an apparently reasonable answer even when the retrieved transactions do not support it.

**Impact**

- Incorrect financial summaries.
- Incorrect category totals.
- User trust issues.
- Potential financial decision errors.

**Recommendation**

Use metadata filtering and structured retrieval where possible. Retrieved records should contain sufficient information such as:

- User identifier.
- Transaction date.
- Category.
- Amount.
- Transaction description.

The final response should be grounded in retrieved records.

---

### 4.2 Financial Calculations Performed by the LLM

**Risk**

An LLM may incorrectly calculate totals, percentages, differences, or remaining budgets.

**Recommendation**

Financial calculations should be performed by deterministic backend logic whenever possible.

For example:

```text
remaining_budget = monthly_budget - total_expenses
```

The LLM should primarily interpret the user's question and explain the result rather than being responsible for critical arithmetic.

---

### 4.3 Hallucinated Financial Information

**Risk**

The assistant may generate a transaction, amount, category, balance, or date that does not exist in the available data.

**Recommendation**

The AI service should:

1. Check whether the required data exists.
2. Retrieve relevant records.
3. Perform deterministic calculations where applicable.
4. Provide only grounded results.
5. Return a clear limitation message when data is unavailable.

---

### 4.4 User Data Isolation

**Risk**

Financial data from one user could accidentally be retrieved for another user if user-level filtering is missing.

**Impact**

This is a high-severity privacy and security risk.

**Recommendation**

Every data-dependent AI request should be associated with the authenticated user context.

Retrieval and database queries should apply user-level filtering before data is passed to the AI layer.

The AI service should never rely on the LLM to enforce data isolation.

---

### 4.5 Invalid or Incomplete Input

Examples include:

- Empty expense descriptions.
- Missing transaction amounts.
- Invalid dates.
- Unknown categories.
- Empty chatbot questions.

**Recommendation**

Validate inputs at the API/service boundary before sending them to an ML model or LLM.

Invalid input should produce a controlled response rather than a model-generated guess.

---

### 4.6 ML Classification Errors

The current expense categorization baseline achieves approximately 78.64% accuracy.

The classification report also shows uneven category-level performance.

Examples:

- Groceries has relatively low precision in the current test.
- Entertainment has lower recall than several other categories.
- Bills and Utilities also show weaker performance than the strongest categories.

**Risk**

A single overall accuracy value can hide poor performance for individual categories.

**Recommendation**

Track per-class Precision, Recall and F1-score in addition to overall accuracy.

Review confusion between similar categories and improve the training data before introducing a more complex model.

---

### 4.7 Unknown or Ambiguous Expenses

Examples:

- `Coffee with colleagues`
- `Payment`
- `Online purchase`
- `Monthly subscription`

**Risk**

The description may not contain enough information to confidently determine the category.

**Recommendation**

Add a confidence-aware fallback such as:

**Needs Review**

Instead of forcing every transaction into a category, low-confidence predictions should be flagged for user review.

---

### 4.8 LLM/API Availability and Cost

**Risk**

External LLM services may introduce:

- Rate limits.
- API failures.
- Increased latency.
- Usage costs.
- Temporary service unavailability.

**Recommendation**

The integration layer should include:

- Timeouts.
- Error handling.
- Controlled retries.
- Safe fallback responses.
- Logging without exposing sensitive financial information.

The application should not expose raw provider errors to users.

---

## 5. Practical Improvement Recommendations

### 5.1 Financial Assistant

Recommended implementation order:

1. Define supported financial intents.
2. Validate incoming requests.
3. Retrieve user-specific financial data.
4. Apply metadata/date/category filters.
5. Perform calculations using backend logic.
6. Use the LLM for interpretation and natural-language response generation.
7. Validate that the response is supported by available data.
8. Return a controlled response to the application.

Avoid adding advanced RAG components before basic retrieval and grounding are validated.

---

### 5.2 RAG Retrieval

Start with:

- Simple vector retrieval.
- Metadata filtering.
- Top-K retrieval.
- Grounded prompts.

Consider hybrid retrieval or reranking only if testing demonstrates that basic retrieval is insufficient.

This keeps the implementation realistic for the Capstone timeline.

---

### 5.3 Expense Categorization

The current TF-IDF + Logistic Regression model is an appropriate baseline.

Before moving to transformers or embeddings:

1. Inspect incorrect predictions.
2. Review category confusion.
3. Improve ambiguous or weak training examples.
4. Validate labels.
5. Evaluate class-level metrics.
6. Add confidence-based review handling.
7. Compare another lightweight model if necessary.

Advanced models should only be introduced if the baseline cannot meet the required performance.

---

## 6. Recommended Service Boundary

The integration layer should separate application concerns from AI/ML concerns.

A conceptual request could be:

```json
{
  "user_id": "authenticated-user",
  "question": "How much did I spend this month?"
}
```

The service should validate the request before passing it to the Financial Assistant.

A conceptual response could be:

```json
{
  "answer": "You spent PKR X this month.",
  "intent": "monthly_expense_total",
  "grounded": true
}
```

The exact API schema should be finalized with the application/backend feature owner.

No credentials, API keys, or private user financial data should be hard-coded into the AI service.

---

## 7. Response Validation

AI-generated responses should pass through a validation stage before reaching the user.

Validation should check:

- Required response fields exist.
- No unsupported financial values were introduced.
- Retrieved data supports the answer.
- User scope is preserved.
- Errors are handled safely.
- The response is relevant to the requested intent.

For deterministic financial operations, the backend-calculated value should be treated as the source of truth.

---

## 8. Coordination Required With Feature Owners

The following areas require coordination rather than duplicate implementation.

| Area | Coordination Required |
|---|---|
| Financial Assistant | Confirm supported intents and chatbot ownership |
| RAG | Confirm retrieval/knowledge-base design |
| Expense Categorization | Confirm final model and prediction interface |
| Backend/API | Confirm request/response schema |
| Authentication | Confirm user identity propagation |
| Database | Confirm transaction and budget fields |
| Validation | Confirm error and fallback behavior |
| Testing | Align integration tests with feature-level tests |
| Deployment | Confirm runtime/model serving approach |

---

## 9. Current Blockers / Open Questions

The following items should be finalized before full AI integration:

1. Final financial transaction schema.
2. Final budget data schema.
3. Authentication/user identity propagation into the AI service.
4. Final Financial Assistant LLM/provider.
5. Final RAG knowledge-base design.
6. Application-facing API contract.
7. Error-response format.
8. Model confidence threshold for expense categorization.
9. Deployment environment for AI services.
10. Logging and monitoring requirements.

These are integration dependencies and should not be assumed to be finalized until confirmed by the relevant feature owners.

---

## 10. Risk Priority

| Risk | Severity | Recommended Mitigation |
|---|---|---|
| Cross-user financial data access | High | Enforce user-level filtering before AI retrieval |
| Hallucinated financial values | High | Grounded retrieval + deterministic calculations |
| Incorrect financial calculations | High | Perform calculations in backend/service logic |
| Incorrect ML category | Medium | Per-class evaluation + confidence fallback |
| Poor RAG retrieval | Medium | Metadata filtering + retrieval evaluation |
| Missing/invalid input | Medium | API validation |
| LLM/API failure | Medium | Timeout, retry and fallback handling |
| High latency/cost | Medium | Limit retrieval/context and monitor usage |
| Ambiguous expense descriptions | Medium | Confidence threshold + Needs Review |
| Unclear API contract | Medium | Coordinate schema before integration |

---

## 11. Capstone-Suitable Implementation Strategy

The recommended approach is incremental.

### Phase 1 — Validate Interfaces

- Finalize request/response schema.
- Confirm user identity propagation.
- Confirm transaction and budget fields.

### Phase 2 — Integrate Existing ML Baseline

- Expose the categorization model through a controlled service interface.
- Validate input.
- Return category and confidence information where supported.

### Phase 3 — Integrate Financial Assistant

- Add intent handling.
- Retrieve user-specific financial information.
- Perform deterministic calculations.
- Use the LLM for natural-language responses.

### Phase 4 — Validate AI Output

- Add grounding checks.
- Add fallback handling.
- Test unsupported and ambiguous queries.
- Test cross-user isolation.

### Phase 5 — Optimize Only Where Needed

Based on test results, consider:

- Better retrieval.
- Hybrid search.
- Reranking.
- Improved ML features.
- Model comparison.

Advanced techniques should not be introduced without evidence that the baseline requires them.

---

## 12. Day 18 Conclusion

The current repository has a useful ML baseline and planning documentation, but the Financial Assistant and AI integration layers are not yet implemented as production-facing services.

The main integration priority is therefore not adding model complexity. It is establishing reliable boundaries between the HisabDo application, backend/API, AI service, retrieval/model layer, and response validation.

The highest-priority risks are:

1. Cross-user financial data leakage.
2. Hallucinated financial information.
3. Incorrect financial calculations.
4. Incorrect or low-confidence expense categorization.
5. Missing API validation and controlled error handling.

The recommended approach is to implement simple, testable service boundaries first and optimize the RAG/ML components only after baseline integration testing identifies a specific limitation.

---

## 13. Evidence / Validation

Repository evidence reviewed:

- `src/financial_assistant/README.md`
- `src/integration/README.md`
- `src/expense_categorization/train_model.py`
- `data/expense_data.csv`
- `research/rag-ml-improvement-research.md`
- `docs/model-evaluation-test-plan.md`

Current ML baseline validation:

- Dataset rows: 500
- Categories: 10
- Unique descriptions: 200
- Accuracy: 78.64%
- Weighted Precision: 85.92%
- Weighted Recall: 78.64%
- Weighted F1-score: 79.03%

The results were obtained by running the existing `train_model.py` implementation locally.

---

## 14. Remaining Work

Pending coordination with feature owners:

- Final API contract.
- Final chatbot/RAG implementation.
- Final database schema.
- Authentication propagation.
- Production deployment approach.
- Integration-level test suite.

This document does not claim completion of those implementation dependencies.

---

## 15. Progress / Evidence Update

### Completed

- Reviewed the current Financial Assistant module structure.
- Reviewed the current AI integration module structure.
- Reviewed the existing Smart Expense Categorization implementation.
- Reviewed the existing RAG/ML improvement research.
- Reviewed the model evaluation/test planning documentation.
- Validated the current ML baseline metrics.
- Identified integration risks and practical mitigations.
- Documented coordination requirements and open technical questions.

### Remaining

- Coordinate the final API contract with the backend/application owner.
- Confirm the final Financial Assistant and RAG implementation.
- Confirm authentication and user-data propagation.
- Perform integration-level testing once the service layer is implemented.

### Blockers / Dependencies

The complete integration cannot be finalized until the application/backend feature owners confirm the API contract, authentication flow, data schema, and AI service implementation.

### Evidence

- Day 18 technical risk and improvement note.
- Existing repository AI/ML modules and documentation.
- Existing expense categorization baseline.
- Local model evaluation results.
- GitHub feature branch and Pull Request.

---

## 16. Security Considerations

The following security requirements should be maintained during implementation:

- Never commit API keys or credentials.
- Do not hard-code secrets in source code.
- Enforce authenticated user context for financial data.
- Prevent cross-user retrieval.
- Avoid exposing sensitive financial information in logs.
- Do not expose system prompts or internal implementation details.
- Validate AI outputs before returning them to the application.
- Do not trust LLM-generated user identifiers or authorization information.

---

## 17. Final Recommendation

For the current Capstone stage, the recommended priority is **reliability before complexity**.

The team should first establish:

**validated input → user-scoped data retrieval → deterministic calculations/model execution → response validation → controlled API response**

Only after this flow is working reliably should the project add advanced RAG retrieval, reranking, hybrid search, transformer-based categorization, or other complexity.

This approach reduces implementation risk while providing a clear path for future improvement based on measurable test results.