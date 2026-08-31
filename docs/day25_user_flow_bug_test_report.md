# Day 25 – User Flow & Bug Testing Report

**Assignee:** Joyce Hany  
**Task:** User Flow & Bug Testing  
**Branch:** `feature/task15-25-workflow-testing-joyce`

---

## 1. Objective

The objective of this task was to test the available AI/ML user flows, validate the existing Smart Expense Categorization functionality, identify issues, and document any blockers affecting end-to-end integration.

The testing focused on:

- Expense data preprocessing
- Expense amount validation
- Smart Expense Categorization baseline model
- Dataset quality and category validation
- Availability of integration/API components
- Availability of Financial Assistant/Chatbot components
- End-to-end workflow readiness

---

## 2. Test Environment

- Repository: `hisabdo-webapp-ai`
- Branch: `feature/task15-25-workflow-testing-joyce`
- Operating System: Windows
- Shell: PowerShell
- Python: Python 3.x
- Main tested module: `src/expense_categorization/`

---

## 3. User Flow Testing

### Flow 1 – Expense Text Preprocessing

**Input:**
```text
  Uber   Trip

The text should be cleaned and normalized by removing unnecessary spaces and converting it to a consistent format.

Actual Result:

uber trip

Status: PASS

Flow 2 – Merchant Normalization

Input:

  UBER

Expected Result:
The merchant name should be normalized to lowercase and unnecessary spaces should be removed.

Expected Output:

uber

Status: PASS

Note: The first PowerShell attempt encountered a console rendering issue before completing the command. This was a PowerShell PSReadLine environment issue and not an application code failure.

Flow 3 – Valid Expense Amount

Input:

250

Expected Result:
The amount should be accepted and converted to a numeric value.

Actual Result:

250.0

Status: PASS

Flow 4 – Negative Expense Amount

Input:

-100

Expected Result:
Negative amounts should be rejected.

Actual Result:

None

Status: PASS

Flow 5 – Invalid Expense Amount

Input:

invalid

Expected Result:
Non-numeric values should be rejected.

Actual Result:

None

Status: PASS

Flow 6 – Smart Expense Categorization Baseline

The baseline experiment was executed using:

python src\expense_categorization\baseline_experiment.py

Actual Result:

Baseline Accuracy: 0.8

The classification report showed predictions for:

Entertainment
Food
Healthcare
Transport

Status: PASS

Note: The baseline was evaluated on a very small sample test set, so the 80% accuracy should not be considered representative of production performance.

Flow 7 – Dataset Validation

The available expense dataset was checked for:

Number of rows
Column names
Missing values
Available categories

Actual Result:

Rows: 500

Columns:
description
amount
category

Missing values:
description    0
amount         0
category       0

The dataset contains 10 categories:

Bills
Education
Entertainment
Food
Groceries
Healthcare
Other
Shopping
Transport
Utilities

Status: PASS

4. End-to-End Integration Testing
Expected Flow
User
  ↓
Enter Expense
  ↓
Backend/API
  ↓
Expense Preprocessing
  ↓
AI Expense Categorization
  ↓
Category Result
  ↓
User
Current Repository Status

The repository currently contains the Smart Expense Categorization preprocessing and baseline model components.

However, the following integration components were not implemented in the current branch during testing:

FastAPI service endpoint
Application integration layer
End-to-end API request/response flow
Connected Financial Assistant/Chatbot implementation

The src/integration/ directory currently contains documentation only, and the src/financial_assistant/ directory currently contains documentation only.

Status: BLOCKED

Reason:
The required integration/API and chatbot implementation is not currently available for full end-to-end execution.

5. Bug / Issue Log
ID	Issue	Severity	Reproduction	Expected	Actual	Status
BUG-001	PowerShell PSReadLine console rendering error	Low	Entered a long Python -c command in PowerShell	Command should be entered normally	PowerShell displayed System.ArgumentOutOfRangeException	Environment issue
BUG-002	Full AI user flow cannot be executed	Medium	Attempted to trace expense → API → AI → response flow	Complete integrated flow should be available	Integration/API implementation is not available	Blocked
BUG-003	Chatbot end-to-end flow cannot be executed	Medium	Attempted to identify chatbot implementation	Chatbot should accept and process user queries	Financial Assistant implementation is not available in the current repository state	Blocked
6. Bug Details
BUG-001 – PowerShell PSReadLine Rendering Error

Description:

PowerShell produced a System.ArgumentOutOfRangeException while entering a long Python command.

Error:

System.ArgumentOutOfRangeException:
The value must be greater than or equal to zero
and less than the console's buffer size in that dimension.

Expected Result:

The command should be accepted and executed normally.

Actual Result:

PowerShell's PSReadLine encountered a console rendering error.

Impact:

No impact on the application code or model functionality.

Classification:

Environment/tooling issue, not an application bug.

Workaround:

The command was retried successfully and the required tests were executed.

BUG-002 – Missing Integration/API Layer

Description:

A complete end-to-end expense categorization flow could not be executed because an implemented FastAPI/application integration layer was not available in the current repository state.

Expected Result:

A user should be able to submit an expense through the application/API and receive an AI-generated category.

Actual Result:

The repository currently contains documentation for the integration layer but no implemented API endpoint was available for execution.

Impact:

Prevents full end-to-end user flow validation.

Status:

Blocked / Pending Integration Implementation.

BUG-003 – Missing Chatbot Implementation

Description:

The Financial Assistant/Chatbot flow could not be executed end-to-end because an implemented chatbot service was not available in the current repository state.

Expected Result:

A user should be able to submit a financial query and receive a validated AI response.

Actual Result:

The src/financial_assistant/ directory currently contains documentation only.

Impact:

Prevents end-to-end chatbot testing.

Status:

Blocked / Pending Chatbot Implementation.

7. Testing Summary
Area	Result
Text preprocessing	PASS
Merchant normalization	PASS
Valid amount validation	PASS
Negative amount validation	PASS
Invalid amount validation	PASS
Baseline categorization	PASS
Dataset validation	PASS
API integration testing	BLOCKED
Chatbot testing	BLOCKED
Full end-to-end user flow	BLOCKED
8. Overall Result

The available Smart Expense Categorization preprocessing and baseline functionality was successfully tested.

The dataset was also validated successfully with 500 records, no missing values, and 10 expense categories.

Full end-to-end testing could not be completed because the API/integration layer and Financial Assistant/Chatbot implementation are not currently available in the repository state used for testing.

The identified PowerShell PSReadLine error was confirmed as an environment/tooling issue rather than an application defect.
9. Recommendations
Implement or connect the FastAPI prediction endpoint.
Connect the expense categorization model to the integration layer.
Implement the Financial Assistant/Chatbot flow.
Add automated API and integration tests under tests/.
Repeat the complete end-to-end workflow once the integration components are available.
Evaluate the categorization model on a larger and more representative test dataset before production use.
10. Evidence

Testing evidence includes:

Successful preprocessing validation
Successful amount validation
Baseline model execution
Baseline accuracy result of 0.80
Dataset validation with 500 records
Missing-value check
Expense category validation
Repository structure inspection
Documented integration and chatbot blockers
Structured bug/issue log