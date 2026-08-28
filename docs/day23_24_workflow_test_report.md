# Day 23–24 – AI User Flow & Workflow Testing Report

## 1. Purpose

This report documents user-flow and workflow testing performed for the currently available AI/ML components in the repository.

The testing focused on the implemented expense categorization and preprocessing workflows.

End-to-end API, chatbot, and application integration testing could not be executed because the current repository contains documentation placeholders for the integration and financial assistant modules but no executable implementation in those directories.

---

## 2. Test Environment

Repository:
`usmankhalid172/hisabdo-webapp-ai`

Branch:
`feature/task23-24-workflow-testing-joyce`

Tested components:

- `src/expense_categorization/baseline_experiment.py`
- `src/expense_categorization/preprocessing.py`
- `data/expense_data.csv`

---

## 3. Test Case 1 – Baseline Expense Classification

### Test

Command:

```text
python src\expense_categorization\baseline_experiment.py
The baseline experiment should execute successfully and produce an accuracy value and classification report.

Actual Result

The experiment executed successfully.

Observed result:

Baseline Accuracy: 0.8

Classification report was generated for:

Entertainment
Food
Healthcare
Transport
Status

PASS

Note

The 80% accuracy is an initial result from the small sample baseline experiment and must not be interpreted as final production model performance.

4. Test Case 2 – Text Preprocessing
Test

Input:

"  Uber   Trip  "

Expected normalized output:

uber trip
Actual Result
clean_text: uber trip
Status

PASS

5. Test Case 3 – Merchant Normalization
Test

Input:

"  UBER  "

Expected:

uber
Actual Result
merchant: uber
Status

PASS

6. Test Case 4 – Valid Amount Validation
Test

Input:

250

Expected:

250.0
Actual Result
valid_amount: 250.0
Status

PASS

7. Test Case 5 – Invalid Amount Validation
Test

Input:

invalid

Expected:

None
Actual Result
invalid_amount: None
Status

PASS

8. Test Case 6 – Negative Amount Validation
Test

Input:

-100

Expected:

None
Actual Result

The preprocessing validation returns None for negative amounts.

Status

PASS

9. Test Case 7 – Dataset Validation
Expected

The dataset should contain the expected fields and valid records.

Actual Result

Rows:

500

Columns:

description
amount
category

Missing values:

description: 0
amount: 0
category: 0
Status

PASS

10. Category Validation

The dataset uses the current team category set:

Food
Groceries
Transport
Utilities
Healthcare
Shopping
Entertainment
Education
Bills
Other

No Transportation or Bills & Utilities category was observed in the validated dataset.

Status

PASS

11. Integration / End-to-End Testing

The repository currently contains README documentation for:

FastAPI integration
AI service/application integration
Financial Assistant / chatbot

However, no executable implementation files were found under:

src/integration/
src/financial_assistant/

Only README files are currently present in those directories.

Therefore, true end-to-end API/chatbot integration testing cannot be executed yet.

Status

BLOCKED / NOT IMPLEMENTED

Reason

Executable integration and chatbot implementations are not currently available in the repository.

12. Bug Log
BUG-001 – End-to-End AI Integration Not Available

Severity: Blocker for E2E testing

Area: AI Service / Application Integration

Steps to Reproduce:

Open src/integration/.
Inspect the available files.
Open src/financial_assistant/.
Inspect the available files.

Expected Result:

Executable API/integration and chatbot components should be available for end-to-end workflow testing.

Actual Result:

Only README documentation is currently present in these directories.

Status:

Blocked / Pending implementation

Impact:

End-to-end user-flow testing across the integrated AI features cannot currently be completed.

13. Testing Summary
Area	Result
Baseline classification	PASS
Text preprocessing	PASS
Merchant normalization	PASS
Valid amount validation	PASS
Invalid amount validation	PASS
Negative amount validation	PASS
Dataset validation	PASS
Category validation	PASS
API integration E2E	BLOCKED
Chatbot E2E	BLOCKED
14. Remaining Work
Test the FastAPI prediction workflow once executable implementation is available.
Test request/response validation.
Test chatbot workflow once executable implementation is available.
Perform full end-to-end integration testing after the AI service and application integration are available.
Re-test any issues identified during integration.
15. Evidence
GitHub branch: feature/task23-24-workflow-testing-joyce
Baseline execution result: 0.80 accuracy on the small sample baseline experiment.
Dataset validation: 500 records, no missing values.
Category validation: current 10-category team taxonomy confirmed.
Preprocessing validation results recorded above.
16. Security Check

No API keys, tokens, passwords, .env secrets, or private credentials were used or committed as part of this testing work.

Only safe project data and synthetic/test inputs were used.