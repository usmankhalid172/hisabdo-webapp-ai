# Day 26 – End-to-End AI User Flow & Bug Testing

**Author:** Joyce Hany

## Objective

Perform end-to-end testing of the available AI workflow components and document the observed behavior, limitations, and potential bugs.

---

# Environment

- Repository: hisabdo-webapp-ai
- Branch: feature/task26-workflow-testing-joyce
- Operating System: Windows
- Python: 3.x

---

# End-to-End Workflow

## Step 1 – Dataset Validation

Result: PASS

Evidence

- Dataset loaded successfully.
- Total rows: 500
- Missing values: 0

---

## Step 2 – Data Preprocessing

Result: PASS

Verified Functions

- clean_text()
- normalize_merchant()
- validate_amount()

Observed Behavior

- Text cleaned successfully.
- Merchant names normalized.
- Invalid amounts rejected.

---

## Step 3 – Baseline Prediction

Result: PASS

Observed Output

Baseline Accuracy: 0.80

Classification categories were produced successfully.

---

## Step 4 – Integration Layer

Result: NOT IMPLEMENTED

Observation

No FastAPI endpoint or integration service exists yet.

---

## Step 5 – AI Chatbot

Result: NOT IMPLEMENTED

Observation

Financial assistant implementation has not yet been added.

---

# Bug Tracking Log

## Bug 1

Title

Integration service unavailable

Severity

Medium

Steps

1. Check src/integration
2. Attempt end-to-end integration

Expected

Working integration layer

Actual

README only

Status

Open

---

## Bug 2

Title

Financial chatbot unavailable

Severity

Medium

Steps

1. Open financial assistant module

Expected

Chatbot implementation

Actual

README only

Status

Open

---

## Bug 3

Title

No automated tests

Severity

Low

Steps

Open tests folder

Expected

Unit tests

Actual

README only

Status

Open

---

# Summary

| Component | Status |
|----------|--------|
| Dataset | PASS |
| Preprocessing | PASS |
| Baseline Model | PASS |
| Integration | NOT IMPLEMENTED |
| Chatbot | NOT IMPLEMENTED |
| Automated Tests | NOT AVAILABLE |

---

# Conclusion

The available AI preprocessing pipeline and baseline expense categorization model function correctly.

The remaining AI integration layer, chatbot implementation, and automated testing framework are not yet available, preventing full end-to-end validation.