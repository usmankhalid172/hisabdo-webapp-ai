# Task 27 – Pre-Release Model Metric Benchmark Logging

**Assignee:** Rimsha Mushtaq
**Responsibility:** Model Evaluation Logging
**Branch:** `feature/task27-model-eval-rimsha`

## 1. Objective

The purpose of this task is to compile post-integration model evaluation metrics and maintain a pre-release benchmark log. The benchmark is used to verify model stability before the final Capstone evaluation.

The evaluation focuses on:

* Accuracy
* Precision
* Recall
* F1-score

## 2. Model Evaluation Benchmark

The current Smart Expense Categorization model uses a TF-IDF text feature extraction pipeline with Logistic Regression classification.

The latest recorded evaluation results are:

| Metric             |  Score |
| ------------------ | -----: |
| Accuracy           | 78.64% |
| Weighted Precision | 85.92% |
| Weighted Recall    | 78.64% |
| Weighted F1-score  | 79.03% |

## 3. Calculation Summary

### Accuracy

Accuracy measures the proportion of correctly classified expense descriptions among all test samples.

**Formula:**

`Accuracy = Correct Predictions / Total Predictions`

Recorded result:

`Accuracy = 0.7864 = 78.64%`

### Precision

Weighted precision measures how accurately the model assigns predictions to the correct categories while accounting for category support.

**Recorded result:**

`Weighted Precision = 0.8592 = 85.92%`

### Recall

Weighted recall measures how effectively the model identifies the correct instances across expense categories.

**Recorded result:**

`Weighted Recall = 0.7864 = 78.64%`

### F1-score

The F1-score combines precision and recall into a single metric using their harmonic mean.

**Formula:**

`F1 = 2 × (Precision × Recall) / (Precision + Recall)`

**Recorded result:**

`Weighted F1-score = 0.7903 = 79.03%`

## 4. Pre-Release Benchmark Interpretation

The model achieved an overall accuracy of **78.64%** on the recorded test set. Weighted precision was higher at **85.92%**, while weighted recall was **78.64%** and weighted F1-score was **79.03%**.

These results indicate that the model provides a reasonable baseline for expense categorization but still has classification weaknesses in some categories.

The higher precision compared with recall indicates that the model's predictions are generally reliable when assigning a category, but some expected categories may still be missed.

## 5. Observed Stability and Failure Patterns

During evaluation, the following failure patterns were observed:

1. **Groceries vs Shopping confusion**

   * Example: `"Bought groceries from supermarket"`
   * Actual model prediction: `Shopping`
   * Expected category: `Groceries`

2. **Entertainment vs Bills confusion**

   * Example: `"Netflix monthly subscription"`
   * Actual model prediction: `Bills`
   * Expected category: `Entertainment`

3. **Ambiguous descriptions**

   * Example: `"Payment for electricity and groceries"`
   * The model may select one category even when the description contains multiple expense types.

4. **Invalid or non-expense inputs**

   * Numeric or random text inputs may still receive an expense category instead of being rejected.

These cases should remain part of future regression testing and pre-release validation.

## 6. Benchmark Status

| Evaluation Area                  | Status   |
| -------------------------------- | -------- |
| Accuracy recorded                | Complete |
| Precision recorded               | Complete |
| Recall recorded                  | Complete |
| F1-score recorded                | Complete |
| Error patterns documented        | Complete |
| Pre-release benchmark documented | Complete |
| Further improvement required     | Yes      |

## 7. Recommendations

Before final Capstone evaluation, the following improvements are recommended:

* Add more representative training examples for frequently confused categories.
* Improve distinction between similar categories such as Groceries and Shopping.
* Review category-label consistency, especially for subscription and entertainment expenses.
* Add validation for empty, numeric, random, or non-expense inputs.
* Continue regression testing after model or dataset changes.
* Track these benchmark metrics after future model updates to identify performance changes.

## 8. Conclusion

The current model has a recorded benchmark of **78.64% accuracy**, **85.92% weighted precision**, **78.64% weighted recall**, and **79.03% weighted F1-score**.

The benchmark provides a reference point for pre-release evaluation. The model is suitable for continued testing, but the documented category-confusion and invalid-input cases should be addressed or monitored before the final Capstone evaluation.

**Pre-release evaluation status: Benchmark documented; improvement and regression monitoring recommended.**
