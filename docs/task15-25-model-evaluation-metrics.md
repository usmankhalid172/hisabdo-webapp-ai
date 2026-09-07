# Model Evaluation Metrics Log

## Task Information

**Task:** Model Evaluation Metric Logging

**Owner:** Rimsha Mushtaq

**Branch:** `feature/task15-25-model-eval-rimsha`

## Evaluation Dataset

The Smart Expense Categorization model was evaluated on a held-out test dataset containing **103 test samples**.

The model uses a TF-IDF text vectorization pipeline with Logistic Regression for expense category prediction.

## Evaluation Metrics

| Metric | Score | Percentage |
|---|---:|---:|
| Accuracy | 0.7864 | 78.64% |
| Weighted Precision | 0.8592 | 85.92% |
| Weighted Recall | 0.7864 | 78.64% |
| Weighted F1-score | 0.7903 | 79.03% |

## Metric Comparison

| Metric | Result | Reliability Observation |
|---|---:|---|
| Accuracy | 78.64% | Correctly classified approximately 78.64% of test samples |
| Weighted Precision | 85.92% | Predicted categories were generally reliable |
| Weighted Recall | 78.64% | Some correct categories were missed |
| Weighted F1-score | 79.03% | Provides a balanced view of precision and recall |

## Category-Level Observations

The evaluation identified confusion between closely related categories, particularly:

- **Groceries vs Shopping**
- **Entertainment vs Bills**

Example errors:

- `"Bought groceries from supermarket"` → **Shopping** instead of **Groceries**
- `"Netflix monthly subscription"` → **Bills** instead of **Entertainment**

## Reliability Assessment

The model provides a useful baseline for automatic expense categorization. However, performance is not uniform across all categories.

Categories with similar meanings and ambiguous descriptions remain more difficult for the model.

## Limitations

- The evaluation dataset is relatively small.
- Performance may vary across categories.
- Ambiguous expense descriptions can lead to incorrect classifications.
- The model currently relies primarily on expense description text.
- Invalid or non-expense inputs require additional validation before classification.

## Deployment Readiness

The current results establish a documented baseline for model reliability.

The **78.64% accuracy** and **79.03% weighted F1-score** indicate useful baseline performance, while the observed category confusion shows that further improvement is recommended before treating the model as fully production-ready.

Recommended improvements include:

1. Increase representative training examples.
2. Improve category balance and coverage.
3. Add more ambiguous real-world expense descriptions to evaluation datasets.
4. Strengthen validation for invalid or non-expense inputs.

## Conclusion

The current Smart Expense Categorization model achieved **78.64% accuracy**, **85.92% weighted precision**, **78.64% weighted recall**, and **79.03% weighted F1-score** on the 103-sample held-out test dataset.

These metrics provide a documented performance baseline and support continued model improvement and validation.