# Task 28 – Pre-Evaluation Model Metric Benchmark Finalization

**Assignee:** Rimsha Mushtaq

**Responsibility:** Model Evaluation Logging

**Branch:** `feature/task28-model-eval-rimsha`

## 1. Objective

The objective of this task is to finalize and document the pre-evaluation benchmark for the Smart Expense Categorization model and reconcile the evaluation evidence with integration-level prediction results.

The evaluation focuses on:

* Accuracy
* Precision
* Recall
* F1-score
* Category-level performance
* Representative integration prediction errors
* Model and dataset traceability

These results provide a reproducible benchmark for the current evaluated model version and support final Capstone project documentation.

## 2. Final Model Evaluation Metrics

The verified evaluation run produced the following overall metrics:

| Metric             |  Score | Percentage |
| ------------------ | -----: | ---------: |
| Accuracy           | 0.7864 |     78.64% |
| Weighted Precision | 0.8592 |     85.92% |
| Weighted Recall    | 0.7864 |     78.64% |
| Weighted F1-score  | 0.7903 |     79.03% |

These values represent the benchmark for the evaluation run documented in this file.

## 3. Metric Consistency and Evaluation Run Clarification

Earlier evaluation evidence and later documentation contained inconsistent category-level metric claims, including references to precision, recall, and F1-score values of `1.00` across primary expense categories.

For this finalized benchmark, the verified overall evaluation results are:

* Accuracy: **78.64%**
* Weighted Precision: **85.92%**
* Weighted Recall: **78.64%**
* Weighted F1-score: **79.03%**

The `1.00` metric claims are **not used as the final model benchmark** because the available evaluation evidence does not provide sufficient model-version, dataset-version, and evaluation-run traceability to reproduce those results.

Therefore, the benchmark in this document is based on the reproducible evaluation run using the current Smart Expense Categorization training pipeline and evaluation dataset described in Section 6.

## 4. Metric Calculations

### Accuracy

Accuracy measures the proportion of correctly classified expense descriptions out of all test samples.

**Result:** `0.7864 = 78.64%`

The model correctly classified approximately 78.64% of the test samples.

### Weighted Precision

Weighted precision measures how many of the predictions assigned to each category were correct while accounting for the number of samples in each category.

**Result:** `0.8592 = 85.92%`

### Weighted Recall

Weighted recall measures how effectively the model identifies the correct category across the test dataset.

**Result:** `0.7864 = 78.64%`

### Weighted F1-score

The F1-score combines precision and recall into a single metric using their harmonic mean.

**Result:** `0.7903 = 79.03%`

## 5. Category-Level Performance

The evaluation showed different performance levels across individual expense categories.

| Category      | Precision | Recall |
| ------------- | --------: | -----: |
| Bills         |      0.62 |      — |
| Education     |      0.67 |   1.00 |
| Entertainment |      1.00 |   0.55 |
| Food          |      1.00 |   0.64 |
| Groceries     |      0.33 |   1.00 |

### Observations

* **Groceries:** High recall but low precision indicates that grocery-related samples were identified, but some predictions assigned to Groceries were incorrect.
* **Entertainment:** High precision but lower recall indicates that Entertainment predictions were generally correct when selected, but some Entertainment examples were missed.
* **Education:** High recall with comparatively lower precision indicates that the model identified Education examples but also produced some false-positive predictions.
* **Bills:** Lower precision indicates that this category may require additional representative training examples.

These category-level values are consistent with the verified overall benchmark and should be treated as the current evaluation evidence.

## 6. Model, Dataset, and Evaluation Run Traceability

The evaluated pipeline used:

* **Model type:** TF-IDF Vectorizer + Logistic Regression
* **TF-IDF features:** Unigrams and bigrams
* **Stop-word removal:** English
* **Classifier:** Logistic Regression
* **Maximum iterations:** 1000
* **Random state:** 42
* **Train/test split:** 80/20 using `train_test_split(test_size=0.20, random_state=42)`

### Dataset

* **Dataset path:** `data/expense_data.csv`
* **Training rows:** 397
* **Testing rows:** 103
* **Unique descriptions:** 200
* **Description overlap:** 0

The absence of description overlap between training and testing data provides a cleaner evaluation of generalization on unseen descriptions.

### Model Artifact

The evaluated model pipeline is saved as:

`model/expense_categorization_pipeline.pkl`

The benchmark in this document refers to the model pipeline and dataset configuration described above. A separate semantic model-version identifier was not available in the existing evaluation artifacts; therefore, the dataset path, model artifact path, preprocessing configuration, classifier configuration, and split parameters are used as the available evaluation-run traceability information.

Future evaluation runs should record a unique model version, dataset version, and evaluation timestamp or run identifier.

## 7. Integration Prediction Analysis

Representative integration predictions were reviewed alongside the benchmark results.

| Input Description                 | Expected Category | Predicted Category | Result    |
| --------------------------------- | ----------------- | ------------------ | --------- |
| Bought groceries from supermarket | Groceries         | Shopping           | Incorrect |
| Bought groceries from Imtiaz      | Groceries         | Shopping           | Incorrect |
| New laptop purchase               | Shopping          | Other              | Incorrect |
| Paid electricity bill             | Utilities         | Utilities          | Correct   |
| Netflix monthly subscription      | Entertainment     | Bills              | Incorrect |

### Main Failure Patterns

#### 1. Groceries vs Shopping confusion

The model may classify grocery-related descriptions as Shopping when the description contains general purchase or shopping-related wording.

Example:

`Bought groceries from Imtiaz` → `Shopping`

Expected category:

`Groceries`

This indicates that additional representative grocery examples and clearer category boundaries may be required.

#### 2. Shopping vs Other confusion

Some general purchase descriptions may be classified as Other instead of Shopping.

Example:

`New laptop purchase` → `Other`

Expected category:

`Shopping`

This suggests that the Shopping category requires additional representative examples covering electronics and other major purchases.

#### 3. Entertainment vs Bills confusion

Subscription-based services may be classified as Bills instead of Entertainment.

Example:

`Netflix monthly subscription` → `Bills`

Expected category:

`Entertainment`

This also highlights the importance of maintaining a consistent category taxonomy across training data, test cases, and documentation.

#### 4. Ambiguous descriptions

Descriptions containing multiple expense concepts may lead to uncertain or inconsistent classifications.

#### 5. Invalid or non-expense inputs

Random, unclear, or non-expense text may still receive an expense category instead of being rejected because the current classification pipeline does not provide a dedicated rejection/unknown mechanism.

## 8. Category Taxonomy Alignment

The evaluation and integration evidence identified cases where expected categories must remain consistent across datasets, test cases, and documentation.

The current benchmark uses the following relevant category distinctions:

* **Groceries:** Food and household grocery purchases.
* **Shopping:** General purchases such as electronics or other non-grocery items.
* **Entertainment:** Services such as Netflix subscriptions and entertainment-related expenses.
* **Bills / Utilities:** Recurring or utility-related payments.

The same category definitions should be used when creating future training examples, integration test cases, and evaluation documentation.

## 9. Performance Interpretation

The final accuracy of **78.64%** indicates that the model provides a useful baseline for automatic expense categorization.

The weighted precision of **85.92%** is higher than recall (**78.64%**), suggesting that the model's predictions are generally reliable when assigning categories, although some relevant categories are missed.

The weighted F1-score of **79.03%** provides a balanced view of precision and recall and represents the overall classification performance of the current evaluation run.

The integration errors identified above demonstrate that overall metrics do not capture every category-specific failure. Therefore, representative prediction testing remains necessary in addition to aggregate evaluation metrics.

## 10. Recommended Improvements

Based on the evaluation and integration QA findings, the following improvements are recommended:

* Increase the number and diversity of training examples.
* Add representative examples for Groceries, Shopping, Bills, and Entertainment.
* Improve separation between Groceries and Shopping.
* Add examples for electronics and other major Shopping purchases.
* Review Netflix and similar subscription examples to ensure consistent Entertainment labeling.
* Standardize category labels across datasets, test payloads, and documentation.
* Add input validation for empty, random, or non-expense descriptions.
* Introduce an unknown/rejection mechanism for unsupported inputs where appropriate.
* Improve handling of ambiguous descriptions containing multiple expense types.
* Record model version, dataset version, evaluation timestamp, and evaluation-run identifier for future benchmarks.
* Evaluate additional classification algorithms for comparison.
* Perform further testing on a larger and more diverse dataset.

## 11. Final Benchmark

| Benchmark          | Final Result |
| ------------------ | -----------: |
| Accuracy           |   **78.64%** |
| Weighted Precision |   **85.92%** |
| Weighted Recall    |   **78.64%** |
| Weighted F1-score  |   **79.03%** |

These values are the finalized benchmark results for the documented evaluation run.

## 12. Conclusion

The Smart Expense Categorization model achieved a final accuracy of **78.64%**, weighted precision of **85.92%**, weighted recall of **78.64%**, and weighted F1-score of **79.03%**.

The evaluation implementation uses an 80/20 train/test split with `random_state=42`, TF-IDF feature extraction, and Logistic Regression. The evaluation dataset contains 397 training rows and 103 testing rows with zero description overlap.

Integration testing identified several category-level errors, particularly:

* Groceries vs Shopping
* Shopping vs Other
* Entertainment vs Bills

These cases are documented as known limitations of the current evaluated model version rather than being presented as resolved issues.

The conflicting `1.00` metric claims from earlier documentation have not been used as the final benchmark because their model-version and evaluation-run traceability could not be established from the available evidence.

The finalized benchmark and known failure cases are documented for re-review and inclusion in the final Capstone project evaluation.
