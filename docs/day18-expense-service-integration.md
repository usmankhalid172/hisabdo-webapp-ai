# Day 18 – Smart Expense Categorization Service Integration

**Prepared by:** Mehar Ali  
**Feature:** Smart Expense Categorization  
**Track:** AI / ML  
**Day:** 18

---

## 1. Service Purpose

The Smart Expense Categorization service provides the integration layer between the application/API and the trained machine learning model.

The service is responsible for:

- Receiving an expense description.
- Validating the input.
- Loading the trained ML pipeline.
- Sending the validated description to the model.
- Returning the predicted expense category.
- Handling invalid input and prediction failures.

The service does not handle:

- User authentication.
- Database operations.
- UI rendering.
- Expense transaction creation.
- Model training.
- Model evaluation.

---

## 2. Service Integration Flow

```text
Application / Client
        |
        | Expense description
        v
AI Service / API
        |
        | Validate request
        v
Categorization Service
        |
        | Validated description
        v
Saved ML Pipeline
        |
        | TF-IDF preprocessing
        v
Logistic Regression Classifier
        |
        | Predicted category
        v
Categorization Service
        |
        | Validated response
        v
AI Service / API
        |
        v
Application / Client
3. Input Contract

The categorization service accepts an expense description.

Field	Type	Required	Description
description	string	Yes	Text describing the expense
Example Input
{
  "description": "Bought groceries from supermarket"
}
Input Validation
Description must be a string.
Description must not be empty.
Leading and trailing whitespace is removed.
Invalid input is rejected before model prediction.
4. Output Contract
Successful Response
{
  "category": "Shopping"
}
Validation Error
{
  "error": "Description cannot be empty."
}
Invalid Data Type
{
  "error": "Description must be a string."
}

If the trained model is unavailable, the service returns a model/service error.

5. Model Integration

The service loads the trained model from:

model/expense_categorization_pipeline.pkl

The saved pipeline contains:

TF-IDF Vectorizer
Logistic Regression Classifier

Prediction flow:

Expense Description
        ↓
TF-IDF Preprocessing
        ↓
Logistic Regression
        ↓
Predicted Category

The model is loaded for prediction and is not retrained during a prediction request.

6. Preprocessing Dependency

The prediction service uses the preprocessing configuration stored inside the trained ML pipeline.

The same preprocessing used during training must be used during prediction to avoid a training/inference mismatch.

Any future preprocessing changes should be coordinated with the preprocessing owner before changing the prediction service.

7. Validation and Error Behavior
Empty Description

Input:

{
  "description": ""
}

Expected behavior:

Reject request
Do not call model
Return validation error

Actual validation result:

ValueError: Description cannot be empty.
Non-String Description

Input:

{
  "description": 123
}

Expected behavior:

Reject request
Do not call model
Return validation error

Actual validation result:

ValueError: Description must be a string.
Whitespace Description

Input:

{
  "description": "   "
}

Expected behavior:

Trim whitespace
Detect empty value
Reject request

Actual validation result:

ValueError: Description cannot be empty.
Missing Model

If the saved model file does not exist:

Prediction cannot continue.
A model/service error should be returned.
8. Sample Prediction Evidence
Sample 1

Input:

{
  "description": "Bought groceries from supermarket"
}

Actual output:

Prediction: Shopping
Sample 2

Input:

{
  "description": "Paid electricity bill"
}

Actual output:

Prediction: Utilities

These predictions were generated locally using the saved ML pipeline through ExpenseCategorizationService.

9. Automated Tests

Test file:

tests/test_prediction_service.py

The tests cover:

Successful prediction.
Empty description validation.
Non-string input validation.
Whitespace-only input validation.

Test command:

pytest tests/test_prediction_service.py -v

Expected successful result:

4 passed
10. Coordination Dependencies
Junaid – API Endpoint Contract

The service expects the API layer to provide an expense description.

The final API request and response structure should follow the shared team endpoint contract.

Full application integration depends on confirmation of the final endpoint contract.

Joyce – Preprocessing

The service depends on the preprocessing included in the saved ML pipeline.

Any changes to text preprocessing, feature extraction, or normalization should be coordinated before modifying the prediction service.

Rimsha – Evaluation

Evaluation results should be used to determine whether prediction quality is suitable for integration.

Evaluation remains a model-quality responsibility rather than a service-layer responsibility.

11. Integration Boundary
INPUT
Expense Description
        ↓
VALIDATION
        ↓
SAVED ML PIPELINE
        ↓
PREDICTION
        ↓
OUTPUT
Predicted Category

The service does not contain application business logic such as:

Creating transactions.
Updating balances.
Database persistence.
User authentication.
UI behavior.
12. Current Blockers / Dependencies

The following dependencies remain:

Final confirmation of Junaid's API endpoint request/response contract.
Confirmation that Joyce's preprocessing requirements are compatible with the saved ML pipeline.
Evaluation findings from Rimsha.
Final agreement on the API error response format.
Current Blocker Status

No blocker prevents local service-level prediction testing.

Full application/API integration remains pending confirmation of the shared team endpoint contract.

13. Files Added
src/expense_categorization/prediction_service.py
tests/test_prediction_service.py
docs/day18-expense-service-integration.md
14. Day 18 Progress Status
Completed
 Defined categorization service purpose and boundaries.
 Defined model input/output contract.
 Mapped model call inside the AI service flow.
 Documented preprocessing/data dependencies.
 Defined validation and error behavior.
 Added service-level prediction implementation.
 Added automated validation tests.
 Documented coordination dependencies.
 Documented blockers.
 Validated sample predictions locally.
Remaining
 Confirm final API contract with Junaid.
 Confirm preprocessing contract with Joyce.
 Incorporate final evaluation findings from Rimsha.
 Complete application-level endpoint integration after the shared API contract is finalized.
15. Overall Status

Local service integration: Completed

Prediction validation: Completed

Automated tests: Completed

Technical documentation: Completed

Full API/application integration: Pending team contract confirmation