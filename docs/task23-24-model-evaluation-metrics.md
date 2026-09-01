# Model Evaluation Metrics Log

## Task Information

**Task:** Model Evaluation Metric Logging

**Owner:** Rimsha Mushtaq

**Branch:** `feature/task23-24-model-eval-rimsha`

## Evaluation Dataset

The trained Smart Expense Categorization model was evaluated on a held-out test dataset containing **103 test samples**.

The model uses a TF-IDF text vectorization pipeline with Logistic Regression for expense category prediction.

## Evaluation Metrics

| Metric             |  Score | Percentage |
| ------------------ | -----: | ---------: |
| Accuracy           | 0.7864 |     78.64% |
| Weighted Precision | 0.8592 |     85.92% |
| Weighted Recall    | 0.7864 |     78.64% |
| Weighted F1-score  | 0.7903 |     79.03% |

## Metric Interpretation

* **Accuracy (78.64%):** The model correctly classified approximately 78.64% of the test samples.
* **Weighted Precision (85.92%):** The model's predicted categories were generally reliable, with higher precision across the weighted category distribution.
* **Weighted Recall (78.64%):** The model successfully identified a substantial proportion of the correct categories, but some categories were missed.
* **Weighted F1-score (79.03%):** The model achieved a balanced overall performance between precision and recall.

## Category-Level Observations

Some categories showed stronger performance than others. The evaluation identified confusion between closely related categories, particularly:

* **Groceries vs Shopping**
* **Entertainment vs Bills**

For example, `"Bought groceries from supermarket"` was predicted as **Shopping** instead of **Groceries**, while `"Netflix monthly subscription"` was predicted as **Bills** instead of **Entertainment**.

## Reliability Assessment

The model provides a useful baseline for automatic expense categorization. However, performance is not uniform across all categories. Categories with similar meanings and ambiguous descriptions remain more difficult for the model.

Further improvement should focus on increasing representative training examples, balancing category coverage, and testing more ambiguous real-world expense descriptions.

## Limitations

* The evaluation dataset is relatively small.
* Performance may vary across categories.
* Ambiguous expense descriptions can lead to incorrect classifications.
* The model currently relies primarily on the expense description text.
* Invalid or non-expense inputs require additional validation before classification.

## Conclusion

The evaluation confirms that the current model achieves **78.64% accuracy** and a **79.03% weighted F1-score** on the held-out test dataset. The results provide a documented baseline for feature reliability and identify areas requiring further model and data improvements.
