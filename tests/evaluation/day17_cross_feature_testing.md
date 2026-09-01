# AI/ML Cross-Feature Testing Results - Day 17

## Ownership

**Prepared by:** Syeda Isma Nazir  
**Responsibility:** Testing / Validation  
**Project:** HisabDo AI/ML Capstone  
**Day:** 17

---

## Testing Scope

Day 17 focused on validating the currently available AI/ML components and identifying features that could not yet be executed because their implementation is not available in the current branch.

The existing testing/evaluation framework was continued.

---

## Test Execution Environment

**Branch:** `feature/syeda-isma-nazir-cross-feature-testing-day-17`

**Environment:**
- Windows PowerShell
- Python 3.14.6
- pandas
- scikit-learn
- joblib

---

## Test Results

| Test ID | Feature | Input / Test | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| TC-17-EXP-001 | Smart Expense Categorization | Execute available training/evaluation script | Model should train successfully and produce evaluation metrics | The executable training script is not available in the current Day 17 branch, so the test could not be executed independently. | NOT TESTED |
| TC-17-EXP-002 | Smart Expense Categorization | Validate available model categories | Evaluation should report category-level precision, recall and F1-score | The executable model is not available in the current Day 17 branch, so category-level evaluation could not be executed. | NOT TESTED |
| TC-17-CHAT-001 | AI Financial Assistant / Chatbot | Attempt feature validation | Chatbot should accept a financial question and return a relevant response | Chatbot implementation is not available in the current branch. | BLOCKED |
| TC-17-API-001 | AI Service / FastAPI | Attempt API validation | API should expose implemented AI endpoints and return structured responses | FastAPI implementation/endpoints are not available in the current branch. | BLOCKED |
| TC-17-API-002 | Expense Categorization API | Validate `/v1/expenses/categorize` | Endpoint should accept an expense request and return a category prediction | Endpoint implementation is not available in the current branch. | BLOCKED |

---

## Model Evaluation Evidence

The Smart Expense Categorization model was successfully executed during Day 16 validation in the separate model test environment.

For Day 17, the model training script is not present in the current `hisabdo-webapp-ai` branch. Therefore, the Day 17 repository does not contain an executable model artifact or training script for independent re-execution.

**Day 17 Status:** NOT TESTED

**Reason:** `src\expense_categorization\train_model.py` is not available in the current branch.

**Previous Evidence:** Day 16 validation recorded 1.00 accuracy on 100 test samples in the separate model test environment. This previous result is referenced for continuity but is not counted as a new Day 17 execution.

### Current Repository Evidence

The current branch contains:

```text
src\expense_categorization\README.md
src\financial_assistant\README.md
src\integration\README.md
tests\README.md
data\README.md

These files provide documentation/placeholders for the relevant components, but executable chatbot, FastAPI, and expense model implementation was not available in the current branch during Day 17 testing.

---

## Evidence and Blockers

### Completed

- Reviewed the current AI/ML repository structure.
- Reviewed the expense categorization component.
- Reviewed the financial assistant/chatbot documentation.
- Reviewed the AI service/integration documentation.
- Reviewed the available testing documentation.
- Attempted to identify executable AI/ML components.
- Recorded test cases using Input, Expected Result, Actual Result and Status.
- Correctly marked unavailable functionality as BLOCKED or NOT TESTED.

### Blocked / Not Tested

- Smart Expense Categorization: **NOT TESTED** on Day 17 because the executable training/model script is unavailable.
- AI Financial Assistant / Chatbot: **BLOCKED** because the implementation is unavailable.
- FastAPI AI Service: **BLOCKED** because the implementation/endpoints are unavailable.
- Expense Categorization API: **BLOCKED** because the endpoint implementation is unavailable.

### Previous Evidence

Day 16 validation recorded:

- Accuracy: **1.00 (100%)**
- Test samples: **100**
- All 10 categories achieved 1.00 precision, recall and F1-score.

This is historical Day 16 evidence and is **not counted as a new Day 17 PASS result**.

---

## Remaining Work

Testing can continue once the relevant AI/ML implementations and API services become available in the shared repository.

The following should be executed when available:

1. Expense categorization model execution.
2. Chatbot functional test cases.
3. FastAPI endpoint tests.
4. Expense categorization API tests.
5. API response validation.
6. Error/invalid-input testing.
7. Screenshot and terminal evidence collection.
8. Consolidated PASS/FAIL/BLOCKED/NOT TESTED report.

---

## Conclusion

Day 17 testing established the current testability status of the available AI/ML components.

No new PASS result was recorded for functionality that could not actually be executed. Previously completed Day 16 evidence is retained only as historical evidence for continuity.

The primary blocker is the absence of executable AI/ML implementations and API services in the current Day 17 branch.