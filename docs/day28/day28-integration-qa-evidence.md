# Day 28 - Integration QA & PR #76 Verification Log

**Project:** HisabDo Web App AI
**Department:** Department 1 - Capstone Development
**Track:** AI/ML
**QA Role:** Integration QA / PR Verification
**QA Engineer:** Syeda Isma Nazir
**QA Branch:** `feature/task28-integration-qa-isma`

---

## 1. QA Workflow

PR #76 was reviewed as part of Day 28 Integration QA.

The review covered:

1. PR scope and changed files.
2. Python compilation.
3. Cleaning-script execution.
4. Dataset validation behavior.
5. Output-data verification.
6. Deployment/environment configuration.
7. Documentation consistency.
8. Code-quality observations.
9. Git diff and repository integration.
10. GitHub PR review decision.

---

## 2. PR #76 Scope

**PR:** #76
**Submitted Branch:** `feature/task28-data-validation-rameesha`
**QA Branch:** `qa-pr-76`
**Author:** Rameesha Zafar

### Changed Files

```text
.env.example
docs/day28-production-dataset-cleaning-and-pipeline-support.md
scripts/day28_production_dataset_cleaning.py
```

The PR introduces production dataset cleaning, validation, normalization, production dataset export logic, Day 28 environment configuration, and supporting documentation.

---

## 3. Repository Scope Verification

The following command was used:

```text
git diff --name-status main...qa-pr-76
```

Result:

```text
M       .env.example
A       docs/day28-production-dataset-cleaning-and-pipeline-support.md
A       scripts/day28_production_dataset_cleaning.py
```

The PR is limited to the expected Day 28 configuration, documentation, and dataset-cleaning utility.

**Status: PASS**

---

## 4. Python Compilation

The submitted script was extracted directly from the Git object and compiled using Python.

The final extraction and compilation were performed using:

```text
git cat-file blob qa-pr-76:scripts/day28_production_dataset_cleaning.py | Set-Content -Path "$env:TEMP\day28_production_dataset_cleaning.py" -Encoding utf8
```

```text
python -m py_compile "$env:TEMP\day28_production_dataset_cleaning.py"
```

The script compiled successfully without syntax errors.

**Status: PASS**

---

## 5. Default Execution Verification

The submitted script uses:

```python
raw_path = os.path.join("data", "sample_transactions.json")
```

The repository was checked for the expected dataset:

```text
git ls-tree -r --name-only qa-pr-76 | Select-String "sample_transactions|cleaned_production"
```

No `sample_transactions.json` or `cleaned_production` dataset was found.

The available data files include:

```text
data/day21_22_ai_sample_payloads.json
data/day21_integration_results.csv
data/day21_integration_test_cases.csv
data/expense_category_sample_payloads.json
data/expense_data.csv
data/faq_docs.json
data/sample_expenses.csv
data/sample_financial_knowledge.json
```

Running the submitted script therefore produced:

```text
[ERROR] Input file not found at 'data\sample_transactions.json'. Generating clean fallback dataset.
```

No fallback dataset is actually generated.

**Status: FAIL**

### Finding

The default execution path references a dataset that is not present in the repository. In addition, the error message states that a fallback dataset is being generated, but the implementation actually returns `False` without generating one.

---

## 6. Controlled Cleaning-Function Execution

A controlled seven-record JSON dataset was supplied to the cleaning function to independently verify its behavior.

The function successfully executed and produced:

```text
Total Input Records Audited: 7
Sanitized Production Records Exported: 4
Duplicate Transactions Removed: 1
Missing Field Anomalies Filtered: 1
Malformed Type Anomalies Resolved: 1
Production Asset Saved To: <temporary QA output>
RETURN: True
```

The test demonstrated that the implementation can:

* Load valid JSON input.
* Detect duplicate transaction IDs.
* Filter missing required fields.
* Filter malformed field types.
* Normalize category values.
* Trim descriptions.
* Export a cleaned JSON file.

**Status: PASS**

---

## 7. Numerical Integrity Verification

The Day 28 documentation states that numerical integrity should enforce positive transaction amounts.

However, the implementation only converts the amount to `float`:

```python
record["amount"] = float(record["amount"])
```

There is no validation rejecting zero or negative amounts.

The controlled QA output contained:

```text
Amounts: [1500.0, -200.0, 0.0, 300.0]
```

Therefore, both `-200.0` and `0.0` remained in the cleaned output.

This contradicts the documented requirement to enforce positive transaction amounts.

**Status: FAIL**

**Severity: Major**

### Finding

Positive transaction amount validation is not implemented.

---

## 8. Output Data Verification

The controlled output contained:

```text
Output records: 4
IDs: ['T001', 'T002', 'T003', 'T005']
Amounts: [1500.0, -200.0, 0.0, 300.0]
Categories: ['Groceries', 'Bills', 'Food', 'Entertainment']
Descriptions: ['Grocery purchase', 'Negative amount', 'Zero amount', 'Movie ticket']
```

Duplicate and malformed records were removed successfully.

However, negative and zero transaction amounts remained in the output.

**Status: PARTIAL PASS**

---

## 9. Deployment Environment Configuration Review

PR #76 adds the following to `.env.example`:

```text
DATASET_PATH=data/cleaned_production_dataset_day28.json
MAX_TRANSACTION_LIMIT=1000
CONFIDENCE_THRESHOLD=0.35
```

Repository inspection showed that:

```text
DATASET_PATH
→ only declared in .env.example

MAX_TRANSACTION_LIMIT
→ only declared in .env.example
```

No application/runtime code was identified consuming these two variables.

The repository also contains different confidence thresholds:

```text
.env.example
CONFIDENCE_THRESHOLD=0.35

src/expense_categorization/prediction_finalizer.py
DEFAULT_CONFIDENCE_THRESHOLD = 0.50

src/expense_categorization/train_model.py
CONFIDENCE_THRESHOLD = 0.30
```

This creates ambiguity regarding which confidence threshold is authoritative at runtime.

**Status: FAIL / NEEDS CLARIFICATION**

**Severity: Moderate**

---

## 10. Deployment Documentation Review

The Day 28 documentation lists deployment-related variables including:

```text
PORT
NODE_ENV
BASE_URL
MONGO_URI
DB_NAME
LLM_API_KEY
MODEL_NAME
VECTOR_DB_URL
EMBEDDING_MODEL
DATASET_PATH
CONFIDENCE_THRESHOLD
```

However, the actual `.env.example` changes in PR #76 add only:

```text
DATASET_PATH
MAX_TRANSACTION_LIMIT
CONFIDENCE_THRESHOLD
```

The documentation therefore does not fully correspond to the configuration changes shown in the PR.

The documentation also does not provide a sufficiently reproducible procedure explaining:

1. Which environment variables are required.
2. Which variables are optional.
3. Where each variable is consumed.
4. How to execute the Day 28 cleaning pipeline.
5. Which input dataset must be supplied.
6. Where the generated cleaned dataset will be stored.

**Status: NEEDS IMPROVEMENT**

---

## 11. Code Quality Review

The following minor code-quality findings were identified:

* `sys` is imported but unused.
* `idx` is created using `enumerate()` but is unused.
* The script assumes every input item is a dictionary and calls `record.get(...)`; a non-object JSON item could therefore raise an unexpected `AttributeError`.
* The missing-input error message incorrectly states that a fallback dataset is being generated.
* The documented positive amount rule is not implemented.

These findings are secondary to the major functional issues.

---

## 12. QA Findings Summary

| Verification                           | Result                     |
| -------------------------------------- | -------------------------- |
| PR scope inspection                    | PASS                       |
| Python compilation                     | PASS                       |
| Controlled cleaning-function execution | PASS                       |
| Duplicate filtering                    | PASS                       |
| Missing-field filtering                | PASS                       |
| Malformed-type filtering               | PASS                       |
| Text normalization                     | PASS                       |
| Default dataset execution              | FAIL                       |
| Positive amount validation             | FAIL                       |
| Deployment variable integration        | FAIL / NEEDS CLARIFICATION |
| Deployment documentation clarity       | NEEDS IMPROVEMENT          |
| Code-quality review                    | FINDINGS IDENTIFIED        |
| Final QA decision                      | **REQUEST CHANGES**        |

---

## 13. Required Changes

Before approval, the following should be addressed:

1. Implement the documented positive transaction amount validation.
2. Add the expected input dataset or correct the default input path.
3. Correct the misleading fallback-dataset error message.
4. Clarify or implement consumption of `DATASET_PATH` and `MAX_TRANSACTION_LIMIT`.
5. Resolve the conflicting `CONFIDENCE_THRESHOLD` values or clearly document which value is authoritative.
6. Update deployment instructions to provide a reproducible setup and execution procedure.
7. Add handling for malformed/non-object JSON records.
8. Re-run QA validation after the changes are pushed.

---

## 14. GitHub Review Decision

A detailed Integration QA review was posted on GitHub PR #76.

### QA DECISION: REQUEST CHANGES

PR #76 demonstrates working basic dataset-cleaning behavior and successfully compiles and executes under controlled input.

However, the implementation does not fully satisfy its documented production-validation requirements.

The most significant issue is that negative and zero transaction amounts remain in the cleaned output despite the documentation stating that positive amounts are enforced.

The default execution path also references a missing dataset, while the newly introduced deployment variables are not demonstrated as being consumed by the application runtime.

The PR should be updated and re-submitted for QA verification before approval.

**Final Status: REQUEST CHANGES**
---

# Day 28 - Integration QA & PR #78 Verification Log

## 15. PR #78 Scope

**PR:** #78

**Submitted Branch:** `qa-pr-78`

**QA Branch:** `feature/task28-integration-qa-isma`

**QA Engineer:** Syeda Isma Nazir

PR #78 was reviewed as part of Day 28 Integration QA and PR verification.

The review focused on:

1. ML training implementation.
2. Train/test split methodology.
3. Dataset size and separation.
4. Description overlap verification.
5. Model configuration.
6. Evaluation metric implementation.
7. Reported metric consistency.
8. Integration prediction behavior.
9. Category-level classification errors.
10. Documentation consistency.
11. GitHub PR review decision.

---

## 16. Model Training and Evaluation Implementation

The submitted `train_model.py` implementation uses:

```python
train_descriptions, test_descriptions = train_test_split(
    unique_descriptions,
    test_size=0.20,
    random_state=42
)
```

The model evaluation code calculates:

```python
accuracy = accuracy_score(y_test, pred)
precision = precision_score(
    y_test,
    pred,
    average="weighted",
    zero_division=0
)
recall = recall_score(
    y_test,
    pred,
    average="weighted",
    zero_division=0
)
f1 = f1_score(
    y_test,
    pred,
    average="weighted",
    zero_division=0
)
```

A classification report is also generated using:

```python
print(classification_report(y_test, pred, zero_division=0))
```

The implementation therefore contains explicit evaluation logic for accuracy, precision, recall, F1-score, and class-level classification reporting.

**Status: PASS**

---

## 17. Train/Test Dataset Separation

The submitted evaluation evidence reports:

```text
Training rows: 397
Testing rows: 103
Unique descriptions: 200
Description overlap: 0
```

The notebook and documentation also contain the corresponding overlap verification.

The reported zero description overlap indicates that identical descriptions were not intentionally shared between the training and testing sets.

**Status: PASS**

---

## 18. Model Configuration Review

The submitted model uses a TF-IDF vectorizer with unigram and bigram features:

```python
TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=1
)
```

The classifier is:

```python
LogisticRegression(
    max_iter=1000
)
```

The training implementation additionally uses:

```python
LogisticRegression(
    max_iter=1000,
    random_state=42
)
```

The model configuration is straightforward and reproducible.

**Status: PASS**

---

## 19. Reported Evaluation Metrics

The reviewed evaluation evidence reports the following category-level metrics:

| Category      | Precision | Recall |   F1 |
| ------------- | --------: | -----: | ---: |
| Bills         |      0.62 |   0.62 | 0.62 |
| Education     |      0.67 |   1.00 | 0.80 |
| Entertainment |      1.00 |   0.55 | 0.71 |
| Food          |      1.00 |   0.64 | 0.78 |
| Groceries     |      0.33 |   1.00 | 0.50 |
| Shopping      |      1.00 |   1.00 | 1.00 |
| Utilities     |      0.50 |   1.00 | 0.67 |

The overall reported results include approximately:

```text
Accuracy: 0.79
Weighted Precision: 0.86
Weighted Recall: 0.79
Weighted F1: 0.79
```

The evidence therefore demonstrates that the model was evaluated on a held-out test set and that category-level performance was recorded.

**Status: PASS**

---

## 20. Evaluation Documentation Consistency Finding

A significant documentation inconsistency was identified.

Earlier evaluation evidence reports category-level performance such as:

```text
Entertainment F1: 0.71
Food F1: 0.78
Groceries F1: 0.50
Utilities F1: 0.67
```

However, later documentation states:

```text
Precision / Recall / F1-Score: 1.00 across all
primary expense categories
```

The later statement does not clearly identify a different model version, dataset, test set, or evaluation run that would explain the improvement.

This creates uncertainty about which metrics represent the actual Day 28 benchmark.

**Status: FAIL / NEEDS CLARIFICATION**

**Severity: Major**

### Finding

The reported evaluation results are inconsistent across the repository.

The model version, dataset version, test set, and execution context associated with the later 1.00 results should be explicitly identified.

---

## 21. Integration Prediction Verification

The available integration evidence was reviewed for representative expense descriptions.

The following cases were identified:

| Description                  | Expected  | Predicted | Confidence | Result            |
| ---------------------------- | --------- | --------- | ---------: | ----------------- |
| Electricity bill payment     | Utilities | Utilities |     0.7411 | Correct           |
| Bought groceries from Imtiaz | Groceries | Shopping  |     0.4410 | Incorrect         |
| Netflix monthly subscription | Bills     | Bills     |     0.2585 | Context-dependent |
| New laptop purchase          | Shopping  | Other     |     0.2499 | Incorrect         |

The electricity example demonstrates a successful Utilities classification.

However, the groceries example was classified as Shopping instead of Groceries, and the laptop purchase was classified as Other instead of Shopping.

These examples demonstrate unresolved classification weaknesses in semantically similar categories.

**Status: PARTIAL PASS**

---

## 22. Category Confusion Findings

The reviewed evidence identifies several category-confusion patterns.

### Groceries vs Shopping

```text
Bought groceries from Imtiaz
Expected: Groceries
Predicted: Shopping
Confidence: 0.4410
```

This indicates that general shopping-related wording can cause the model to favor Shopping over Groceries.

### Shopping vs Other

```text
New laptop purchase
Expected: Shopping
Predicted: Other
Confidence: 0.2499
```

This indicates weak classification confidence for a common Shopping transaction.

### Entertainment vs Bills

Earlier evaluation evidence also contains:

```text
Netflix monthly subscription
Expected: Entertainment
Predicted: Bills
```

Other integration evidence treats Bills as the expected category for the same description, creating an additional taxonomy/documentation inconsistency that should be clarified.

**Status: NEEDS IMPROVEMENT**

---

## 23. Code and Reproducibility Review

The core ML implementation contains explicit and reproducible model settings.

The train/test split uses:

```text
test_size = 0.20
random_state = 42
```

The classifier uses Logistic Regression with a defined maximum iteration count.

The evaluation code explicitly calculates standard classification metrics.

The repository also contains notebook output and supporting documentation corresponding to the reported 397/103 train/test split.

**Status: PASS**

---

## 24. Documentation Review

The PR contains extensive documentation describing model evaluation, category performance, integration behavior, and subsequent improvement work.

However, the documentation needs better version/run traceability.

In particular, when different documents report substantially different metrics, the documentation should identify:

1. Model version/configuration.
2. Dataset version.
3. Training/test split.
4. Evaluation date or run.
5. Whether the result is baseline, fine-tuned, or post-processing performance.
6. Whether the result comes from offline evaluation or integration testing.

Without these identifiers, it is difficult to determine which reported benchmark should be treated as authoritative.

**Status: NEEDS IMPROVEMENT**

---

## 25. QA Findings Summary - PR #78

| Verification                         | Result                     |
| ------------------------------------ | -------------------------- |
| PR scope inspection                  | PASS                       |
| Train/test split verification        | PASS                       |
| Dataset-size verification            | PASS                       |
| Description-overlap verification     | PASS                       |
| TF-IDF configuration                 | PASS                       |
| Logistic Regression configuration    | PASS                       |
| Evaluation metric implementation     | PASS                       |
| Classification report generation     | PASS                       |
| Reported baseline metrics            | PASS                       |
| Metric/documentation consistency     | FAIL / NEEDS CLARIFICATION |
| Integration prediction verification  | PARTIAL PASS               |
| Groceries vs Shopping classification | FAIL                       |
| Shopping vs Other classification     | FAIL                       |
| Category taxonomy consistency        | NEEDS IMPROVEMENT          |
| Documentation reproducibility        | NEEDS IMPROVEMENT          |
| Final QA decision                    | **REQUEST CHANGES**        |

---

## 26. Required Changes for PR #78

Before approval, the following should be addressed:

1. Reconcile the conflicting evaluation metrics reported across the repository.

2. Clearly identify the model version, dataset, test set, and evaluation run associated with each benchmark.

3. Correct or improve the Groceries vs Shopping classification issue.

4. Investigate the `New laptop purchase → Other` classification and ensure that expected category mappings are consistent.

5. Clarify whether `Netflix monthly subscription` belongs to Bills or Entertainment according to the project's authoritative category taxonomy.

6. Ensure that integration-test expectations and model-evaluation documentation use the same category taxonomy.

7. Clearly distinguish baseline, fine-tuned, and post-processing evaluation results.

8. Re-run the relevant evaluation/integration tests after changes and update the documented evidence.

---

## 27. GitHub Review Decision - PR #78

A detailed Integration QA review was posted on GitHub PR #78.

### QA DECISION: REQUEST CHANGES

PR #78 contains a valid and reproducible ML training/evaluation implementation, including explicit train/test splitting, TF-IDF feature extraction, Logistic Regression classification, and standard evaluation metrics.

However, the repository contains inconsistent evaluation claims and unresolved integration-level classification issues.

The most significant QA concern is the discrepancy between the earlier category-level benchmark results and later documentation claiming 1.00 precision, recall, and F1 across primary categories without clearly identifying a different evaluation run or model version.

Integration evidence also demonstrates incorrect classifications for representative transactions such as groceries and laptop purchases.

The PR should therefore be updated to reconcile the reported metrics, align the category taxonomy across documentation and tests, and address the identified classification issues before final approval.

**Final Status: REQUEST CHANGES**

---

# Day 28 Combined QA Status

| PR  | Author / Branch      | QA Status           | Main Findings                                                                                                                  |
| --- | -------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| #76 | Rameesha Zafar       | **REQUEST CHANGES** | Missing default dataset, missing positive-amount validation, deployment configuration/documentation issues                     |
| #78 | Task 28 ML benchmark | **REQUEST CHANGES** | Conflicting evaluation metrics, category-taxonomy inconsistencies, Groceries/Shopping and Shopping/Other classification issues |

Both reviewed PRs currently require changes before QA approval.
