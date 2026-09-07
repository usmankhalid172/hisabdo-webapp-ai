# Task 26 – Model Evaluation Logging

## Objective

Record model evaluation metrics across the test dataset to document model reliability and deployment readiness.

## Model Evaluation Summary

The Smart Expense Categorization model was evaluated using a TF-IDF feature extraction pipeline with Logistic Regression.

| Metric | Score |
|---|---:|
| Accuracy | 78.64% |
| Weighted Precision | 85.92% |
| Weighted Recall | 78.64% |
| Weighted F1-score | 79.03% |

## Evaluation Dataset

| Dataset | Rows |
|---|---:|
| Training Set | 397 |
| Test Set | 103 |
| Total | 500 |

The test set contained descriptions that did not overlap with the training descriptions.

## Category-Level Performance

| Category | Precision | Recall |
|---|---:|---:|
| Bills | 0.62 | — |
| Education | 0.67 | 1.00 |
| Entertainment | 1.00 | 0.55 |
| Food | 1.00 | 0.64 |
| Groceries | 0.33 | 1.00 |

## Evaluation Calculation Logs

The following metrics were recorded from model evaluation:

- Accuracy = 0.7864
- Weighted Precision = 0.8592
- Weighted Recall = 0.7864
- Weighted F1-score = 0.7903

These values correspond to:

- Accuracy: 78.64%
- Precision: 85.92%
- Recall: 78.64%
- F1-score: 79.03%

## Reliability Findings

The model demonstrates reasonable overall performance, with an accuracy of 78.64% and weighted F1-score of 79.03%.

However, category-level results show that some expense categories are more difficult to distinguish than others. In particular, Groceries and Shopping can be confused, while Entertainment and Bills may also overlap for subscription-related descriptions.

## Known Evaluation Failures

Examples observed during testing include:

| Input | Expected | Predicted | Result |
|---|---|---|---|
| Bought groceries from supermarket | Groceries | Shopping | Incorrect |
| Paid electricity bill | Utilities | Utilities | Correct |
| Netflix monthly subscription | Entertainment | Bills | Incorrect |

These failures indicate that additional training examples and clearer category boundaries may improve model performance.

## Deployment Readiness

The current model can be considered suitable for prototype-level evaluation but should not yet be treated as fully reliable for production deployment.

Recommended improvements:

1. Add more representative training examples.
2. Increase coverage of ambiguous expense descriptions.
3. Improve separation between similar categories such as Groceries vs Shopping.
4. Add validation for empty, invalid, or non-expense inputs.
5. Continue monitoring model performance using the same evaluation metrics.

## Conclusion

The model evaluation results have been logged to provide a measurable benchmark for future improvements.

Current benchmark:

**Accuracy: 78.64% | Precision: 85.92% | Recall: 78.64% | F1-score: 79.03%**

The results provide a baseline for tracking future model improvements and assessing readiness for deployment.