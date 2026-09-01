# Smart Expense Categorization – AI/ML Roadmap and Technical Status

## 1. Overview

The Smart Expense Categorization workstream aims to automatically classify user expenses into appropriate categories using machine learning.

The current work has progressed from planning and preprocessing requirements to a small baseline ML experiment, use-case documentation, and integration preparation.

The current baseline approach uses TF-IDF text features with Logistic Regression.

---

## 2. Completed

### Day 15 – Planning

Completed the initial Smart Expense Categorization planning work.

The planning work defined:

- Expense-data preprocessing requirements.
- Candidate input features.
- A simple baseline-model approach.
- Initial model input considerations.
- Expected development requirements.

**Documentation:**

`docs/smart_expense_categorization_plan.md`

---

### Day 16 – AI Prototype / POC

Implemented preprocessing and a small baseline experiment.

**Implementation files:**

- `src/expense_categorization/preprocessing.py`
- `src/expense_categorization/baseline_experiment.py`

The preprocessing component supports:

- Expense description cleaning.
- Lowercase normalization.
- Whitespace normalization.
- Merchant normalization.
- Amount validation.
- Duplicate handling.

The baseline experiment uses:

```text
Expense Description + Merchant
            |
            v
          TF-IDF
            |
            v
  Logistic Regression
            |
            v
   Predicted Category
```
Observed baseline accuracy: 80%

The result is an initial proof-of-concept result only because the sample dataset is very small.

### Day 17 – AI Use Case Documentation

Documented the Smart Expense Categorization use case including:

Problem statement.
Proposed AI solution.
Required input data.
Processing/model approach.
Expected output.
HisabDo integration point.
Testing and evaluation approach.
Risks and limitations.

Documentation:

docs/smart_expense_categorization_use_case.md

 ### Day 18 – Integration Preparation

Prepared sample expense-category payloads and integration notes.

Sample payload file:

data/expense_category_sample_payloads.json

Integration documentation:

docs/smart_expense_integration_notes.md

The sample payloads cover:

Valid expense requests.
Missing description.
Negative amount.
Missing merchant.
Invalid amount type.

The integration notes also document:

Request structure.
Expected response.
Input validation rules.
Error-handling considerations.
Security/privacy requirements.
Dependencies.
Known blockers.
## 3. In Progress

The following work remains in progress:

Integration of the baseline model with the prediction API.
Validation of the final API request/response contract.
Testing the model with a larger and more representative dataset.
Evaluation of additional candidate input features.
End-to-end integration testing with the HisabDo application.

The current baseline is considered a prototype and not a production-ready model.

## 4. Pending

The following items are pending:

Connect the preprocessing/model pipeline to the prediction API.
Finalize the API request and response schema.
Evaluate the model using a larger approved dataset.
Improve model performance using additional relevant features if justified.
Perform broader testing and error analysis.
Complete application-level integration.
Perform end-to-end testing.
Confirm production-readiness requirements.
## 5. Current Baseline Results

The current baseline experiment achieved:

**Baseline Accuracy: 80%**

This result was obtained using a very small synthetic sample dataset and is intended only as an initial proof-of-concept result.

The 80% accuracy does not represent the final model performance and should not be considered production-level performance.

The classification report showed:

| Category      | Precision | Recall | F1-score |
| ------------- | --------: | -----: | -------: |
| Entertainment |      0.50 |   1.00 |     0.67 |
| Food          |      1.00 |   1.00 |     1.00 |
| Healthcare    |      1.00 |   0.50 |     0.67 |
| Transport     |      1.00 |   1.00 |     1.00 |

A larger and more representative approved dataset is required for meaningful model evaluation.

## 6. Blockers


### GitHub Status

The previous GitHub permission issue (403) has been resolved.

The feature branch has been successfully pushed to the shared repository, and Pull Request #5 is currently under Team Lead review.

No GitHub access blocker remains. 
Dataset Availability

A larger approved dataset is required for reliable model evaluation.

Only safe synthetic/sample data should be used until an approved real dataset and privacy/storage approach are confirmed.

API Integration

The final prediction API contract and integration with the application are handled by the relevant API/integration owners and are still pending.

## 7. Testing Status
Completed
Preprocessing component execution.
Baseline model execution.
Sample-data validation.
Classification evaluation using accuracy, precision, recall, and F1-score.
Basic input validation scenarios.
Pending
Testing with a larger dataset.
Additional edge-case testing.
API endpoint testing.
End-to-end application integration testing.
Production-level evaluation.
## 8. Documentation Status

Completed documentation includes:

docs/smart_expense_categorization_plan.md
docs/smart_expense_categorization_use_case.md
docs/smart_expense_integration_notes.md
docs/smart_expense_categorization_roadmap.md

Implementation documentation and experiment evidence are linked to the corresponding source files.

## 9. GitHub / PR Status

The Smart Expense Categorization work is being developed on the feature branch:

feature/joyce-smart-expense-plan

Local commits completed so far include:

Day 15 planning commit.
Day 16 preprocessing/baseline commit.
Day 17 use-case documentation commit.
Day 18 integration preparation commit.


Once repository access is resolved:

Push the feature branch.
Verify all related commits and files.
Open a Pull Request to main.
Request Team Lead review.
Address review comments if required.
Merge only after approval.
## 10. Next Steps Toward Day 30

The planned next steps are:

#### Step 1 – Complete the review process 

Complete the review process and merge PR #5 after approval.
#### Step 2 – Complete API Integration

Connect the preprocessing and baseline model to the prediction API.

#### Step 3 – Improve Dataset

Replace or extend the small prototype sample with a larger approved dataset.

#### Step 4 – Improve Features

Evaluate whether additional features such as:

Amount
Date/time
Payment method
Currency
Merchant information

improve classification performance.

#### Step 5 – Evaluate the Model

Run broader evaluation using:

Accuracy
Precision
Recall
F1-score
Confusion matrix
Edge-case analysis
#### Step 6 – End-to-End Testing

Validate the following flow:
```
HisabDo Application
        |
        v
Backend/API
        |
        v
Expense Categorization Service
        |
        v
Preprocessing
        |
        v
ML Model
        |
        v
Validated Prediction
        |
        v
HisabDo Application
```
#### Step 7 – Production Readiness

Before production use, confirm:

Approved dataset and privacy approach.
Stable API contract.
Input validation.
Error handling.
Model evaluation.
Logging and monitoring requirements.
Security requirements.
Performance and latency requirements.
## 11. Remaining Smart Expense Categorization Work

The remaining work for the Smart Expense Categorization stream includes:

Final API integration.
Larger approved dataset preparation.
Model evaluation on representative data.
Feature improvement.
Edge-case testing.
End-to-end testing.
Application integration.
Production-readiness validation.

The current preprocessing and baseline implementation provides the initial ML foundation for these next stages.

## 12. Current Status Summary
Area	Status
Planning	Completed
Preprocessing	Completed
Baseline ML experiment	Completed
Initial evaluation	Completed
Use-case documentation	Completed
Integration payload preparation	Completed
API integration	Pending
Larger dataset	Pending
Advanced evaluation	Pending
Application integration	Pending
End-to-end testing	Pending
GitHub push — Completed
Pull Request — Open (PR #5) / Under Team Lead Review
---

## Day 19 Evidence

The Day 19 contribution consolidates the current Smart Expense Categorization progress and provides a technical roadmap toward the next development stages.

### Completed in Day 19

- Summarized the completed preprocessing and baseline-model work.
- Documented the current baseline experiment result.
- Documented current integration status and dependencies.
- Documented testing status and known limitations.
- Documented GitHub/PR status and the repository access blocker.
- Defined remaining work and next steps toward Day 30.
- Mapped the Smart Expense Categorization work from Day 15 through Day 19 to the corresponding files and contributions.

### Day 19 Deliverable

Primary documentation:

`docs/smart_expense_categorization_roadmap.md`

This document serves as the Day 19 technical status and roadmap evidence for the Smart Expense Categorization workstream.
---

## Day-wise Contribution and Evidence

| Day | File / Evidence | Contribution |
|-----|-----------------|--------------|
| Day 15 | `docs/smart_expense_categorization_plan.md` | Defined expense-data preprocessing requirements, candidate input features, and baseline-model approach. |
| Day 16 | `src/expense_categorization/preprocessing.py` | Implemented expense preprocessing and input validation support. |
| Day 16 | `src/expense_categorization/baseline_experiment.py` | Implemented and executed the small baseline ML experiment using TF-IDF and Logistic Regression. |
| Day 17 | `docs/smart_expense_categorization_use_case.md` | Documented the Smart Expense Categorization AI use case. |
| Day 18 | `docs/smart_expense_integration_notes.md` | Documented integration requirements, payload structure, validation, errors, security, and dependencies. |
| Day 18 | `data/expense_category_sample_payloads.json` | Added safe synthetic sample payloads for integration testing. |
| Day 19 | `docs/smart_expense_categorization_roadmap.md` | Consolidated technical status, completed work, blockers, testing status, and roadmap toward Day 30. |