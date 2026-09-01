# Day 21–22 – Data Preparation & Workflow Support

## 1. Purpose

This document records the data preparation, sample payload, preprocessing, and schema requirements prepared to support the ready AI workflows.

The focus is on supporting chatbot, expense classification, and prediction workflows without duplicating previously completed AI/ML implementation work.

---

## 2. Existing Data and Artifacts Reused

The following existing project artifacts were reviewed and reused as references:

- `data/expense_category_sample_payloads.json`
- `data/expense_data.csv`
- `src/expense_categorization/preprocessing.py`
- `src/expense_categorization/baseline_experiment.py`
- `docs/smart_expense_integration_notes.md`

Existing files were not modified as part of this Day 21–22 work.

The existing dataset contains 500 expense records and uses the following fields:

- `description`
- `amount`
- `category`

---

## 3. Supported Expense Categories

Sample and validation data must follow the current team category set exactly:

1. Food
2. Groceries
3. Transport
4. Utilities
5. Healthcare
6. Shopping
7. Entertainment
8. Education
9. Bills
10. Other

Category naming should remain consistent across datasets, preprocessing, model outputs, and integration payloads.

In particular:

- Use `Transport`, not `Transportation`.
- Keep `Bills` and `Utilities` as separate categories.
- Do not use `Bills & Utilities`.

---

## 4. API/Input Payload Schema

The reviewed expense input payload uses the following fields:

| Field | Type | Purpose |
|---|---|---|
| `expense_description` | string | Description of the expense |
| `merchant` | string | Merchant or service provider |
| `amount` | number | Expense amount |
| `currency` | string | Currency code |
| `payment_method` | string | Payment method |

The `category` field is not required as an input for classification/prediction requests because it represents the expected classification output.

---

## 5. Dataset Schema

The existing sample dataset uses:

| Field | Type | Purpose |
|---|---|---|
| `description` | string | Expense description |
| `amount` | numeric | Expense amount |
| `category` | string | Target expense category |

The dataset schema and API payload schema are not identical.

The integration layer should therefore map the API input field `expense_description` to the dataset/model feature `description` where required.

The `merchant` field is available in the API payload and is used by the existing baseline text feature preparation.

---

## 6. Preprocessing Requirements

The existing preprocessing implementation was reviewed for integration support.

Current preprocessing behavior includes:

- Convert expense descriptions to lowercase.
- Trim leading and trailing whitespace.
- Normalize repeated whitespace.
- Normalize merchant names using the same text cleaning process.
- Convert expense amounts to numeric values.
- Reject negative amounts.
- Return invalid numeric values as `None`.
- Remove duplicate records.

The existing preprocessing implementation was reused as-is and was not duplicated or replaced for this task.

---

## 7. Baseline Model Input

The existing baseline experiment combines:

- `expense_description`
- `merchant`

into a single text feature.

The baseline then uses:

- TF-IDF vectorization
- Logistic Regression

The `amount` field is validated during preprocessing but is not currently used as a baseline text-model feature.

The `currency` and `payment_method` fields are available in the input payload but are not currently used by the existing baseline text classifier.

These fields should only be added as model features if the final model design explicitly requires them.

---

## 8. Day 21–22 Sample Payloads

A new sample payload file was prepared:

`data/day21_22_ai_sample_payloads.json`

It contains safe synthetic examples for:

- Classification
- Prediction
- Chatbot workflow support

The payload file was validated as valid JSON before use.

No API keys, tokens, passwords, `.env` secrets, or private data are included.

---

## 9. Workflow Support

### Classification

Input:

- expense description
- merchant
- amount
- currency
- payment method

The data can be validated and preprocessed before being passed to the classification workflow.

### Prediction

Prediction samples use the same input format and do not include a preassigned category.

The category is expected to be produced by the prediction/model workflow.

### Chatbot

Chatbot examples contain a natural-language user message plus structured expense information where available.

The structured fields can be used by the downstream expense workflow after extraction/validation.

---

## 10. Validation Requirements

Before integration, incoming expense data should be checked for:

- Missing or empty expense descriptions.
- Invalid or negative amounts.
- Invalid amount types.
- Missing merchant values where merchant information is required.
- Unsupported category values in labeled datasets.
- Consistent field names and data types.

Invalid records should be rejected, corrected, or routed for validation according to the final API contract.

---

## 11. Integration Format Requirements

The integration layer should preserve a clear separation between:

1. Raw/API input
2. Preprocessed model input
3. Model prediction
4. Final user-facing response

Field names should be mapped consistently between the API payload and the dataset/model schema.

The final production API contract should be confirmed with the integration/backend team before implementation.

---

## 12. Dependencies

This data preparation work depends on:

- The approved expense categorization model.
- The final API/integration contract.
- The final production dataset.
- The model input/output schema.
- The chatbot or prediction workflow requirements.

The prepared payloads are intended for integration testing and workflow support and do not replace the final production dataset or model.

---

## 13. Limitations

The existing baseline experiment is an initial baseline using a small sample dataset.

Any previously observed baseline accuracy, including the 80% result, must be interpreted only as a small-sample baseline experiment result.

It must not be presented as final production model performance.

The prepared synthetic payloads are for development, validation, and integration support only.

---

## 14. Day 21–22 Completion Evidence

### Completed

- Reviewed existing expense dataset structure.
- Confirmed the current 10-category team taxonomy.
- Reviewed existing preprocessing behavior.
- Reviewed existing baseline model inputs.
- Prepared new synthetic AI workflow sample payloads.
- Added classification, prediction, and chatbot sample inputs.
- Validated the new payload file as valid JSON.
- Documented dataset/API schema differences.
- Documented preprocessing and integration requirements.
- Documented dependencies and limitations.

### Remaining

- Final production API contract confirmation.
- Integration with the approved production model.
- Validation against the final production dataset/model.
- End-to-end integration testing after the backend/integration workflow is ready.

### Current Blocker / Dependency

No blocker in preparing the sample payloads and preprocessing documentation.

Final integration depends on the approved production model, final API contract, and integration workflow.

---

## 15. Files Added for Day 21–22

- `data/day21_22_ai_sample_payloads.json`
- `docs/day21_22_data_preparation_notes.md`

Existing Day 15–20 implementation files were reused as references and were not duplicated or replaced.