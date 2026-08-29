\# Task 28 – Pre-Evaluation Model Metric Benchmark Finalization



\*\*Assignee:\*\* Rimsha Mushtaq

\*\*Responsibility:\*\* Model Evaluation Logging

\*\*Branch:\*\* `feature/task28-model-eval-rimsha`



\## 1. Objective



The objective of this task is to finalize and document the post-integration evaluation metrics for the Smart Expense Categorization model.



The evaluation focuses on:



\* Accuracy

\* Precision

\* Recall

\* F1-score



These metrics provide a consolidated benchmark of the model's performance for inclusion in the final Capstone project documentation.



\## 2. Final Model Evaluation Metrics



| Metric             |  Score | Percentage |

| ------------------ | -----: | ---------: |

| Accuracy           | 0.7864 |     78.64% |

| Weighted Precision | 0.8592 |     85.92% |

| Weighted Recall    | 0.7864 |     78.64% |

| Weighted F1-score  | 0.7903 |     79.03% |



\## 3. Metric Calculations



\### Accuracy



Accuracy measures the proportion of correctly classified expense descriptions out of all test samples.



\*\*Result:\*\* `0.7864 = 78.64%`



The model correctly classified approximately 78.64% of the test samples.



\### Weighted Precision



Weighted precision measures how many of the predictions assigned to each category were correct while accounting for the number of samples in each category.



\*\*Result:\*\* `0.8592 = 85.92%`



\### Weighted Recall



Weighted recall measures how effectively the model identifies the correct category across the test dataset.



\*\*Result:\*\* `0.7864 = 78.64%`



\### Weighted F1-score



The F1-score combines precision and recall into a single metric using their harmonic mean.



\*\*Result:\*\* `0.7903 = 79.03%`



\## 4. Category-Level Performance



The evaluation showed differences in performance across individual expense categories.



| Category      | Precision | Recall |

| ------------- | --------: | -----: |

| Bills         |      0.62 |      — |

| Education     |      0.67 |   1.00 |

| Entertainment |      1.00 |   0.55 |

| Food          |      1.00 |   0.64 |

| Groceries     |      0.33 |   1.00 |



\### Observations



\* \*\*Groceries:\*\* High recall but low precision, indicating that grocery-related samples were identified but some other samples were also classified as Groceries.

\* \*\*Entertainment:\*\* High precision but lower recall, meaning Entertainment predictions were generally correct, but some Entertainment examples were missed.

\* \*\*Education:\*\* High recall with comparatively lower precision.

\* \*\*Bills:\*\* Lower precision indicates that this category may require additional representative training examples.



\## 5. Error Analysis



Representative predictions observed during testing:



| Input Description                 | Expected Category | Predicted Category | Result    |

| --------------------------------- | ----------------- | ------------------ | --------- |

| Bought groceries from supermarket | Groceries         | Shopping           | Incorrect |

| Paid electricity bill             | Utilities         | Utilities          | Correct   |

| Netflix monthly subscription      | Entertainment     | Bills              | Incorrect |



\### Main Failure Patterns



1\. \*\*Groceries vs Shopping confusion\*\*

&#x20;  Descriptions containing general shopping-related wording may be classified as Shopping instead of Groceries.



2\. \*\*Entertainment vs Bills confusion\*\*

&#x20;  Subscription-based services such as Netflix may be classified as Bills instead of Entertainment.



3\. \*\*Ambiguous descriptions\*\*

&#x20;  Inputs containing multiple expense concepts can lead to uncertain classifications.



4\. \*\*Invalid or non-expense inputs\*\*

&#x20;  Random or unclear text may still receive an expense category instead of being rejected.



\## 6. Model and Dataset Information



The evaluated pipeline used:



\* TF-IDF Vectorizer

\* Unigram and bigram features

\* English stop-word removal

\* Logistic Regression classifier

\* Maximum iterations: 1000

\* Random state: 42



Evaluation dataset information:



\* \*\*Training rows:\*\* 397

\* \*\*Testing rows:\*\* 103

\* \*\*Unique descriptions:\*\* 200

\* \*\*Description overlap:\*\* 0



The absence of description overlap between training and testing data provides a cleaner evaluation of generalization on unseen descriptions.



\## 7. Performance Interpretation



The final accuracy of \*\*78.64%\*\* indicates that the model provides a reasonable baseline for automatic expense categorization.



The weighted precision of \*\*85.92%\*\* is higher than recall (\*\*78.64%\*\*), suggesting that the model's predictions are generally reliable, although some relevant categories are missed.



The weighted F1-score of \*\*79.03%\*\* provides a balanced view of precision and recall and represents the overall classification performance of the current model.



\## 8. Recommended Improvements



Based on the evaluation and observed errors, the following improvements are recommended:



\* Increase the number and diversity of training examples.

\* Add more representative examples for confusing categories such as Groceries, Shopping, Bills, and Entertainment.

\* Review and standardize category labels across datasets and test payloads.

\* Add input validation for empty, random, or non-expense descriptions.

\* Improve handling of ambiguous descriptions containing multiple expense types.

\* Evaluate additional classification algorithms for comparison.

\* Perform further testing on a larger and more diverse dataset.



\## 9. Final Benchmark



| Benchmark          | Final Result |

| ------------------ | -----------: |

| Accuracy           |   \*\*78.64%\*\* |

| Weighted Precision |   \*\*85.92%\*\* |

| Weighted Recall    |   \*\*78.64%\*\* |

| Weighted F1-score  |   \*\*79.03%\*\* |



\## 10. Conclusion



The Smart Expense Categorization model achieved a final accuracy of \*\*78.64%\*\*, weighted precision of \*\*85.92%\*\*, weighted recall of \*\*78.64%\*\*, and weighted F1-score of \*\*79.03%\*\*.



The model demonstrates a useful baseline for automated expense categorization. However, category-level errors, ambiguous descriptions, and invalid inputs remain areas for improvement.



These final benchmark results and observed failure cases are documented for inclusion in the final Capstone project evaluation and documentation.



