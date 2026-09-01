# Day 19 — Smart Expense Categorization Technical Status & Roadmap

**Prepared by:** Mehar Ali
**Feature:** Smart Expense Categorization
**Track:** AI / ML
**Day:** 19
**Repository:** `hisabdo-webapp-ai`

---

## 1. Purpose

This document records the current technical status of the Smart Expense Categorization feature as of Day 19.

It summarizes:

* Completed design, model, and service work.
* Current model behavior and evaluation results.
* Prediction and testing evidence.
* API/application integration status.
* Dependencies and known limitations.
* Completed, in-progress, pending, and blocked work.
* Roadmap from Day 19 toward Day 30.

---

## 2. Completed Work

### Design and Planning

* Smart Expense Categorization was selected as the primary AI/ML feature.
* The feature input/output contract and integration boundaries were documented.
* The proposed ML approach uses supervised text classification.
* The model architecture uses TF-IDF text features with Logistic Regression.

### Dataset and Model

* Current dataset contains **500 expense records**.
* There are **10 expense categories**.
* Each category contains **50 records**.
* Current categories:

  * Bills
  * Education
  * Entertainment
  * Food
  * Groceries
  * Healthcare
  * Other
  * Shopping
  * Transport
  * Utilities
* The training script splits unique descriptions before creating the train/test datasets.
* Current training run contains **397 training rows** and **103 testing rows**.
* There was **0 description overlap** between the training and testing sets.

### Prediction Service

Day 18 added the service-level prediction integration:

`src/expense_categorization/prediction_service.py`

The service:

* Accepts an expense description.
* Validates the input type.
* Rejects empty descriptions.
* Trims leading and trailing whitespace.
* Loads the saved ML pipeline.
* Sends the description to the model.
* Returns the predicted category.
* Handles missing model files.

The locally saved model is:

`model/expense_categorization_pipeline.pkl`

### Automated Testing

Day 18 added:

`tests/test_prediction_service.py`

The tests cover:

1. Successful prediction.
2. Empty description rejection.
3. Non-string input rejection.
4. Whitespace-only description rejection.

Actual test result:

```text
4 passed in 2.55s
```

---

## 3. Current Model Architecture

The current model uses a scikit-learn pipeline:

```text
Expense Description
        |
        v
TF-IDF Vectorizer
        |
        v
Logistic Regression
        |
        v
Predicted Expense Category
```

### TF-IDF Configuration

* Lowercase conversion: enabled
* English stop words: enabled
* N-gram range: `(1, 2)`

### Logistic Regression Configuration

* `max_iter=1000`
* `random_state=42`

The complete pipeline is saved using Joblib and reused during prediction.

---

## 4. Current Model Evaluation

The latest local training run produced:

| Metric                         | Result |
| ------------------------------ | -----: |
| Accuracy                       | 78.64% |
| Precision                      | 85.92% |
| Recall                         | 78.64% |
| F1-score                       | 79.03% |
| Training rows                  |    397 |
| Testing rows                   |    103 |
| Unique descriptions            |    200 |
| Train/test description overlap |      0 |

### Classification Observations

Some categories currently perform strongly:

* Healthcare: F1 = 1.00
* Shopping: F1 = 1.00
* Education: F1 = 0.80
* Other: F1 = 0.86
* Transport: F1 = 0.82

Some categories require further improvement:

* Groceries: F1 = 0.50
* Bills: F1 = 0.62
* Utilities: F1 = 0.67
* Entertainment: F1 = 0.71

These results indicate that the baseline model is functional but still requires further validation and improvement before production use.

---

## 5. Actual Prediction Evidence

The current saved model was tested with several realistic expense descriptions.

| Input                             | Actual Prediction |
| --------------------------------- | ----------------- |
| Bought groceries from supermarket | Shopping          |
| Paid electricity bill             | Utilities         |
| Uber ride to office               | Transport         |
| Bought medicine from pharmacy     | Healthcare        |
| Monthly internet bill             | Bills             |

These predictions confirm that the saved pipeline can process normal expense descriptions and return categories.

### Unusual Input Evidence

The model was also tested with vague or unrelated descriptions:

| Input                   | Prediction |
| ----------------------- | ---------- |
| xyz abc random purchase | Other      |
| something               | Healthcare |
| paid for stuff          | Utilities  |
| hello world             | Healthcare |

This demonstrates an important limitation: the current classifier always produces a category even when the input is vague or unrelated.

---

## 6. Prediction Service Validation

The service layer performs validation before calling the ML model.

### Valid Input

```text
Input:
Bought groceries from supermarket

Result:
Shopping
```

### Empty Input

```text
Input:
""

Result:
ValueError: Description cannot be empty.
```

### Whitespace Input

```text
Input:
"   "

Result:
ValueError: Description cannot be empty.
```

### Non-String Input

```text
Input:
123

Result:
ValueError: Description must be a string.
```

The raw ML model itself does not provide this validation. The validation is implemented by the prediction service.

---

## 7. API / Application Integration Status

### Completed

**Service-level ML integration is completed.**

The prediction service provides the integration boundary between an application/API layer and the saved ML model.

### Pending

Full application/API integration is **not yet completed**.

The current Day 19 branch does not contain a FastAPI endpoint or frontend connection for Smart Expense Categorization.

The following remain pending:

* Final API request/response contract.
* API endpoint implementation.
* Connecting the API endpoint to `ExpenseCategorizationService`.
* Connecting the application/frontend expense flow to the API.
* Returning the predicted category to the user.
* End-to-end application testing.

Therefore, the feature should currently be considered:

**ML model + prediction service: Functional**

**Full web application integration: Pending**

---

## 8. Dependencies

The feature currently depends on:

* Python 3.10 environment.
* pandas.
* scikit-learn.
* joblib.
* pytest for automated testing.
* The trained model file:
  `model/expense_categorization_pipeline.pkl`
* The expense dataset:
  `data/expense_data.csv`

The prediction service also depends on the preprocessing configuration stored inside the trained ML pipeline.

Any future preprocessing changes should be coordinated with the model/training work to avoid training and inference mismatch.

---

## 9. Known Limitations

### 9.1 Model Accuracy

The current accuracy is approximately **78.64%**.

This is acceptable as a baseline POC but should be improved or further validated before production deployment.

### 9.2 Small Dataset

The current dataset contains only **500 records**.

Although the category distribution is balanced, the dataset is relatively small for a production expense categorization system.

### 9.3 Ambiguous Input

The model returns a category even for vague or unrelated descriptions.

There is currently no:

* Confidence threshold.
* `Unknown` category.
* Human review fallback.
* Low-confidence prediction response.

### 9.4 Category Confusion

The evaluation results show weaker performance for some categories, particularly:

* Groceries
* Bills
* Utilities
* Entertainment

Further data and feature improvement may be required.

### 9.5 Limited Input Features

The current prediction service uses only the expense description.

Potential future features such as:

* Merchant name.
* Amount.
* Payment method.
* Transaction metadata.

are not currently used by the model.

### 9.6 No Production API Integration

The ML service is not yet connected to the complete HisabDo application flow.

---

## 10. Current Work Status

### Completed

* [x] Smart Expense Categorization design completed.
* [x] Dataset prepared.
* [x] Baseline ML model implemented.
* [x] TF-IDF + Logistic Regression pipeline implemented.
* [x] Model evaluation implemented.
* [x] Saved model pipeline generated.
* [x] Prediction service implemented.
* [x] Service input validation implemented.
* [x] Prediction service automated tests completed.
* [x] Sample predictions verified.
* [x] Day 19 technical status documented.


### Pending

* [x] Final API request/response contract.
* [x] FastAPI/API endpoint implementation.
* [x] Application/frontend integration.
* [x] End-to-end API testing.
* [x] Improved handling of uncertain predictions.
* [x] Further model evaluation and improvement.
* [x] Final production-readiness validation.

### Blocked

**No technical blocker currently prevents local ML prediction or service-level testing.**

Full application integration may depend on confirmation of the shared team API contract.

---

## 11. Day 19 → Day 30 Roadmap

### Day 19 — Technical Status

* Document current model and service status.
* Record actual prediction evidence.
* Record evaluation metrics.
* Record testing status.
* Identify limitations and dependencies.
* Define remaining roadmap.

### Day 20–22 — Model Improvement and Validation

Planned work:

* Review misclassified categories.
* Analyze weak-performing categories.
* Add or improve representative training examples where appropriate.
* Test additional expense descriptions.
* Re-evaluate accuracy, precision, recall, and F1-score.
* Investigate confidence/uncertainty handling.

### Day 23–25 — API Integration

Planned work:

* Finalize shared API request/response contract.
* Implement the API endpoint.
* Connect the endpoint to `ExpenseCategorizationService`.
* Validate request data.
* Return predicted category through the API.
* Handle model/service errors consistently.

Target flow:

```text
HisabDo Web Application
        |
        v
Expense API Endpoint
        |
        v
ExpenseCategorizationService
        |
        v
Saved ML Pipeline
        |
        v
Predicted Category
        |
        v
API Response
        |
        v
HisabDo Application
```

### Day 26–28 — Integration Testing

Planned testing:

* Valid expense descriptions.
* Empty descriptions.
* Whitespace-only descriptions.
* Invalid data types.
* Unusual descriptions.
* API error responses.
* Model loading failures.
* End-to-end application/API flow.

### Day 29 — Final Validation and Documentation

Planned work:

* Final model evaluation.
* Final API testing.
* Record prediction evidence.
* Document limitations.
* Update technical documentation.
* Confirm integration status.
* Prepare demonstration evidence.

### Day 30 — Final Feature Readiness

Target outcome:

```text
Expense Input
     ↓
HisabDo Application
     ↓
API
     ↓
Prediction Service
     ↓
ML Model
     ↓
Expense Category
     ↓
Application Response
```

The feature should have documented model performance, tested integration, known limitations, and clear evidence of working predictions.

---

## 12. Evidence Summary

### Model Evidence

Latest training run:

```text
Training rows: 397
Testing rows: 103
Unique descriptions: 200
Description overlap: 0

Accuracy: 0.7864077669902912
Precision: 0.8592233009708737
Recall: 0.7864077669902912
F1-score: 0.7903350990103262
```

### Prediction Evidence

```text
Bought groceries from supermarket -> Shopping
Paid electricity bill -> Utilities
Uber ride to office -> Transport
Bought medicine from pharmacy -> Healthcare
Monthly internet bill -> Bills
```

### Test Evidence

```text
pytest tests/test_prediction_service.py -v

4 passed in 2.55s
```

### Repository Evidence

Day 18 service integration commit:

```text
0c16ff8
mehar-ali-service-integration-day18
```

Day 19 branch:

```text
feature/mehar-ali-expense-roadmap-day-19
```

---

## 13. GitHub Links

### Repository

https://github.com/usmankhalid172/hisabdo-webapp-ai

### Day 19 Branch

`feature/mehar-ali-expense-roadmap-day-19`


## 14. Final Day 19 Status

**Current status: Functional ML prediction service with pending full application/API integration.**

The Smart Expense Categorization feature has a working baseline ML pipeline, a service-level prediction layer, automated validation tests, and verified sample predictions.

The current baseline achieves approximately **78.64% accuracy** and **79.03% weighted F1-score** on the current test split.

The main remaining work toward Day 30 is model improvement/validation, API integration, application integration, end-to-end testing, and final production-readiness documentation.
