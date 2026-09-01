# Smart Expense Categorization – Day 20 Validation

## 1. Objective

Day 20 focuses on finalizing data preprocessing and baseline-model support for the Smart Expense Categorization workstream.

The work continues the preprocessing and baseline responsibilities established during Days 15–19.

The purpose of this validation is to confirm that sample inputs, preprocessing requirements, candidate model features, and the baseline experiment are aligned with the planned expense-category API flow.

---

## 2. Work Completed

The following preprocessing and baseline-support components have been reviewed and validated:

- Expense description cleaning.
- Lowercase text normalization.
- Whitespace normalization.
- Merchant normalization.
- Amount validation.
- Duplicate handling.
- Sample expense-category payload validation.
- Candidate model input review.
- Baseline experiment review.
- Alignment between preprocessing inputs and the planned API request structure.

---

## 3. Preprocessing Component

The preprocessing implementation is located at:

`src/expense_categorization/preprocessing.py`

The current preprocessing component supports:

- Cleaning expense descriptions.
- Converting text to lowercase.
- Normalizing whitespace.
- Normalizing merchant values.
- Validating amount values.
- Handling duplicate records.

The preprocessing stage is intended to prepare valid inputs before they are passed to the baseline model or future prediction API.

---

## 4. Sample Input Validation

The sample expense-category payloads are located at:

`data/expense_category_sample_payloads.json`

The sample payloads are synthetic development/test data only.

They cover representative validation scenarios including:

- Valid expense requests.
- Missing expense descriptions.
- Missing merchant values.
- Negative amounts.
- Invalid amount values.

No real financial records, personal data, credentials, or production exports are included.

---

## 5. Candidate Model Input Features

The current baseline primarily uses text information from:

- `expense_description`
- `merchant`

The `amount` field is validated during preprocessing but is not currently used as a feature in the baseline text classifier.

Other fields such as:

- `currency`
- `payment_method`
- `date/time`

may be considered as future candidate features or service-level validation fields.

Additional features should only be included after evaluation demonstrates that they improve model performance.

---

## 6. Baseline Model Support

The baseline experiment is located at:

`src/expense_categorization/baseline_experiment.py`

The current baseline pipeline is:

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

The baseline experiment was successfully executed using safe sample data.

Observed baseline accuracy:

**80%**

This 80% result is from the small sample baseline experiment only.

It must not be treated as final model performance or production-level accuracy.

A larger and representative approved dataset is required for meaningful model evaluation.

---

## 7. Category Alignment

The current team category set is:

- Food
- Groceries
- Transport
- Utilities
- Healthcare
- Shopping
- Entertainment
- Education
- Bills
- Other

The preprocessing, sample inputs, documentation, and future API/model integration should use these category names consistently.

In particular:

- `Transport` should be used instead of `Transportation`.
- `Bills` and `Utilities` should remain separate.
- `Groceries` should be included as a supported category.

---

## 8. Planned API Flow Validation

The expected integration flow is:

User
  |
  v
HisabDo Application
  |
  v
Backend / API
  |
  v
Expense Categorization Service
  |
  v
Preprocessing
  |
  v
Baseline / Main Categorization Model
  |
  v
Validated Prediction
  |
  v
HisabDo Application

The current preprocessing inputs are compatible with the planned expense-category request structure.

The final prediction API request and response contract remains the responsibility of the API/integration owners.

---

## 9. Dependencies

The current work depends on:

- The main expense categorization model.
- An approved and sufficiently representative dataset.
- The prediction API endpoint.
- API request/response validation.
- Application integration.

The baseline implementation is intended as a support/prototype component and does not replace the main production categorization model.

---

## 10. Work Still Remaining

The following work remains:

- Integration with the main categorization model.
- Integration with the prediction API.
- Evaluation using a larger approved dataset.
- Evaluation of additional candidate features.
- Broader edge-case testing.
- End-to-end application testing.
- Production-readiness validation.

---

## 11. Current Blockers / Limitations

Current limitations include:

- The baseline experiment uses a small sample dataset.
- The final approved training dataset has not yet been established.
- The final prediction API contract is handled by the API/integration owners.
- The main categorization model is owned by the relevant model owner.

The 80% baseline accuracy should therefore be considered an initial prototype result only.

---

## 12. Validation Evidence

Relevant evidence includes:

- Preprocessing implementation:
  `src/expense_categorization/preprocessing.py`

- Baseline experiment:
  `src/expense_categorization/baseline_experiment.py`

- Sample payloads:
  `data/expense_category_sample_payloads.json`

- Previous planning documentation:
  `docs/smart_expense_categorization_plan.md`

- Use-case documentation:
  `docs/smart_expense_categorization_use_case.md`

- Integration documentation:
  `docs/smart_expense_integration_notes.md`

- Roadmap and technical status:
  `docs/smart_expense_categorization_roadmap.md`

---

## 13. Day 20 Progress Summary

### Completed

- Reviewed preprocessing requirements.
- Validated sample expense-category inputs.
- Reviewed candidate model input features.
- Validated the baseline experiment.
- Confirmed the baseline result is reproducible.
- Reviewed alignment with the planned API flow.
- Confirmed category naming consistency with the current team category set.

### Remaining

- Main model integration.
- Prediction API integration.
- Larger approved dataset evaluation.
- Additional feature evaluation.
- Broader testing.
- End-to-end integration testing.

### Blockers / Dependencies

- Main categorization model dependency.
- Approved representative dataset dependency.
- Prediction API integration dependency.

### Evidence

All relevant source files, sample payloads, baseline results, and documentation are maintained in the Day 20 feature branch and will be submitted through the corresponding Pull Request.