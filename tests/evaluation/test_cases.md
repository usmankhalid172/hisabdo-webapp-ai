## Ownership

**Prepared by:** Syeda Isma Nazir  
**Responsibility:** Structured Testing / Evaluation Template and Evidence Format  
**Project:** HisabDo AI/ML Capstone  
**Phase:** Day 15–19

# AI/ML Structured Test Cases

## Purpose

This document provides structured test cases for evaluating the AI/ML features developed for the HisabDo capstone project.

The test cases are designed to check:

- Valid inputs
- Invalid inputs
- Empty or incomplete inputs
- Expected AI behavior
- Error handling
- Response correctness

---

## Test Case Format

| Field | Description |
|---|---|
| Test ID | Unique identifier |
| Feature | AI/ML feature being tested |
| Test Type | Functional, validation, error handling, etc. |
| Input | Data/request provided to the system |
| Expected Result | Expected system behavior |
| Actual Result | Result observed during testing |
| Status | PASS / FAIL / BLOCKED / NOT TESTED |
| Evidence | Screenshot, API response, log, or other proof |
| Notes | Additional observations |

---

## Smart Expense Categorization

### TC-EXP-001 — Valid Food Expense

**Feature:** Smart Expense Categorization  
**Test Type:** Functional  
**Input:** `Bought groceries from supermarket`  
**Expected Result:** Expense should be categorized as `Food & Groceries`  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** Screenshot/API response  
**Notes:** Basic valid expense description.

---

### TC-EXP-002 — Valid Transportation Expense

**Feature:** Smart Expense Categorization  
**Test Type:** Functional  
**Input:** `Petrol for car`  
**Expected Result:** Expense should be categorized as `Transportation`  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** Screenshot/API response  
**Notes:** Tests a common transportation expense.

---

### TC-EXP-003 — Valid Healthcare Expense

**Feature:** Smart Expense Categorization  
**Test Type:** Functional  
**Input:** `Purchased medicine from pharmacy`  
**Expected Result:** Expense should be categorized as `Healthcare`  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** Screenshot/API response  
**Notes:** Tests healthcare-related terminology.

---

### TC-EXP-004 — Empty Description

**Feature:** Smart Expense Categorization  
**Test Type:** Input Validation  
**Input:** Empty description  
**Expected Result:** System should reject the request or return a clear validation error.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** API error response/screenshot  
**Notes:** Checks required input validation.

---

### TC-EXP-005 — Very Short Description

**Feature:** Smart Expense Categorization  
**Test Type:** Input Validation  
**Input:** `x`  
**Expected Result:** System should reject the input or handle it safely without producing an unreliable prediction.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** API response/screenshot  
**Notes:** Tests insufficient input information.

---

### TC-EXP-006 — Ambiguous Expense

**Feature:** Smart Expense Categorization  
**Test Type:** Robustness  
**Input:** `Payment`  
**Expected Result:** System should handle the ambiguous description safely. If confidence handling is available, a low-confidence result should be identified.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** API response/screenshot  
**Notes:** Tests an unclear expense description.

---

## AI Financial Assistant / Chatbot

### TC-CHAT-001 — Valid Financial Question

**Feature:** AI Financial Assistant  
**Test Type:** Functional  
**Input:** `How can I reduce my monthly food expenses?`  
**Expected Result:** System should provide a relevant financial response without inventing personal financial information.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** Chat response screenshot  
**Notes:** Tests a normal financial question.

---

### TC-CHAT-002 — Empty Question

**Feature:** AI Financial Assistant  
**Test Type:** Input Validation  
**Input:** Empty message  
**Expected Result:** System should reject the request or ask the user to provide a question.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** Screenshot/API response  
**Notes:** Checks empty-input handling.

---

### TC-CHAT-003 — Unsupported Request

**Feature:** AI Financial Assistant  
**Test Type:** Error Handling  
**Input:** A request unrelated to supported financial functionality  
**Expected Result:** System should respond safely and indicate the supported scope instead of generating an unrelated answer.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** Screenshot/API response  
**Notes:** Tests scope handling.

---

## API / Service Validation

### TC-API-001 — Valid Request

**Feature:** AI Service/API  
**Test Type:** API Validation  
**Input:** Valid request according to the API schema  
**Expected Result:** API should return a successful structured response.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** API response/Postman or Swagger screenshot  
**Notes:** Basic API functionality test.

---

### TC-API-002 — Missing Required Field

**Feature:** AI Service/API  
**Test Type:** Validation  
**Input:** Request with a required field removed  
**Expected Result:** API should return a validation error with an appropriate HTTP status.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** Error response/screenshot  
**Notes:** Tests schema validation.

---

### TC-API-003 — Invalid Data Type

**Feature:** AI Service/API  
**Test Type:** Validation  
**Input:** Incorrect data type for a required field  
**Expected Result:** API should reject invalid input and return a clear validation response.  
**Actual Result:** To be recorded during testing  
**Status:** To be recorded  
**Evidence:** API error response  
**Notes:** Tests input type validation.

---

## Evidence Requirements

For each completed test case, provide at least one relevant piece of evidence.

Acceptable evidence includes:

- Swagger screenshot
- Postman screenshot
- API request/response
- Terminal test output
- Model evaluation output
- Application screenshot
- Test log

Evidence should clearly show the feature, input, and resulting output whenever possible.

---

## Test Status

Use only the following statuses:

- **PASS** — Expected behavior was observed.
- **FAIL** — Actual behavior did not meet the expected result.
- **BLOCKED** — Testing could not be completed because of a dependency or technical issue.
- **NOT TESTED** — Test has been defined but not executed yet.