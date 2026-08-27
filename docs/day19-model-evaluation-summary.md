\# Rimsha Mushtaq â€“ Model Evaluation Summary \& Failure Cases â€“ Day 19



\*\*Workstream:\*\* Smart Expense Categorization

\*\*Responsibility:\*\* Consolidate model evaluation status, testing results, known failure cases, and remaining evaluation work.



\## 1. Evaluation Overview



This document consolidates the existing Smart Expense Categorization evaluation work from Day 15, Day 16, and Day 18 and adds the baseline model evaluation that was executable in the current repository.



The evaluation status has changed since Day 16. At that time, the model was unavailable for executable evaluation. A baseline Logistic Regression text-classification experiment is now available and was executed successfully.



No evaluation results are reported unless the corresponding test or experiment was actually executed.



\## 2. Work Completed



The following evaluation work has been completed:



\* Existing model evaluation and testing criteria from Day 15 were reviewed.

\* Day 16 evaluation and edge-case work was reviewed and its previous blocker was carried forward.

\* The available Smart Expense Categorization baseline experiment was executed.

\* Baseline model performance metrics were recorded.

\* Individual test-set predictions were inspected.

\* One actual incorrect prediction was identified and documented.

\* Day 18 integration test cases and their blocker status were reviewed.

\* Existing valid, ambiguous, invalid, and edge-case payload definitions were reviewed.

\* Remaining evaluation gaps and blockers were identified.



\## 3. Baseline Model Evaluation



The current baseline experiment uses TF-IDF text features generated from the combined expense description and merchant fields and trains a Logistic Regression classifier.



The available sample dataset contains 12 labeled expense records. A stratified train/test split was used with 34% of the data assigned to the test set.



The executed evaluation produced the following results:



| Metric             |     Result |

| ------------------ | ---------: |

| Accuracy           | 0.80 (80%) |

| Macro Precision    |       0.88 |

| Macro Recall       |       0.88 |

| Macro F1-Score     |       0.83 |

| Weighted Precision |       0.90 |

| Weighted Recall    |       0.80 |

| Weighted F1-Score  |       0.80 |

| Test Samples       |          5 |



\### Per-Category Results



| Category      | Precision | Recall | F1-Score | Support |

| ------------- | --------: | -----: | -------: | ------: |

| Entertainment |      1.00 |   1.00 |     1.00 |       1 |

| Food          |      0.50 |   1.00 |     0.67 |       1 |

| Healthcare    |      1.00 |   0.50 |     0.67 |       2 |

| Transport     |      1.00 |   1.00 |     1.00 |       1 |



The baseline achieved 80% accuracy, with four of five test predictions classified correctly.



\## 4. Actual Test Predictions



The executed baseline evaluation produced the following test-set results:



| Input                          | Expected Category | Predicted Category | Result        |

| ------------------------------ | ----------------- | ------------------ | ------------- |

| `netflix monthly plan netflix` | Entertainment     | Entertainment      | Correct       |

| `doctor clinic clinic`         | Healthcare        | Food               | \*\*Incorrect\*\* |

| `medical pharmacy pharmacy`    | Healthcare        | Healthcare         | Correct       |

| `mcdonalds meal mcdonalds`     | Food              | Food               | Correct       |

| `uber taxi uber`               | Transport         | Transport          | Correct       |



\## 5. Known Failure Case



\### Failure Case 1 â€“ Healthcare Misclassified as Food



\*\*Input:\*\* `doctor clinic clinic`



\*\*Expected Category:\*\* Healthcare



\*\*Predicted Category:\*\* Food



\*\*Result:\*\* Incorrect



\*\*Likely cause:\*\* The baseline model is trained on a very small sample dataset. The available healthcare examples may not provide enough representative text patterns for all healthcare-related descriptions. The model may therefore associate some words or text patterns with another category such as Food.



\*\*Evidence:\*\* This error was directly observed in the executed baseline test output.



\*\*Recommended improvement:\*\*



\* Expand the training dataset with more healthcare descriptions.

\* Include a wider range of healthcare-related merchants and descriptions.

\* Add more representative examples of doctor, clinic, hospital, pharmacy, and medical transactions.

\* Re-evaluate the model after increasing the training data.



The cause above is an evaluation hypothesis and has not been independently proven.



\## 6. Confusion Matrix Status



A confusion matrix was \*\*not generated\*\* by the current baseline experiment.



The current experiment calculates Accuracy and Classification Report metrics but does not call a confusion-matrix evaluation function.



\*\*Status:\*\* NOT AVAILABLE



A confusion matrix should be generated during the next evaluation iteration to identify category-level confusion patterns more clearly.



\## 7. Normal Testing Status



\### Model-Level Normal Testing



The baseline test set included normal expense examples such as:



\* Netflix subscription

\* Doctor/clinic expense

\* Medical pharmacy expense

\* McDonald's meal

\* Uber taxi



These model-level predictions were actually executed and are reported in Section 4.



\*\*Status:\*\* COMPLETED for the available baseline test set.



\### Broader Normal Test Cases



The Day 18 integration test plan also contains broader normal cases such as groceries, utilities, education, shopping, bills, and healthcare.



Those integration cases were \*\*not executed\*\*.



\*\*Status:\*\* NOT TESTED



\## 8. Ambiguous Testing Status



Ambiguous cases were defined in the existing test plans, including examples such as:



\* `Payment for electricity and groceries`

\* `Apple`

\* `Store purchase`

\* Similar or unclear expense descriptions



However, no executed prediction results for these ambiguous cases were found in the available evaluation evidence.



\*\*Status:\*\* NOT TESTED



These cases should be executed once the appropriate prediction/API flow is available.



\## 9. Edge-Case and Validation Testing Status



The repository contains defined validation examples including:



\* Missing expense description

\* Negative amount

\* Missing merchant

\* Invalid amount type

\* Very short or unclear descriptions

\* Empty input

\* Random or invalid text



The Day 18 integration test plan also defines edge cases such as:



\* `123456789`

\* `xyz random payment`

\* `!!!`

\* Empty input



These cases are documented as planned tests, but their execution has not been verified.



\*\*Status:\*\* NOT TESTED



The following should therefore not be considered completed:



\* Invalid input testing

\* Empty input testing

\* Negative amount testing

\* Invalid amount type testing

\* Ambiguous-input handling

\* Edge-case prediction testing



\## 10. Day 18 Integration Testing Status



The Day 18 integration test document defines 16 integration test cases covering valid, ambiguous, invalid, and edge-case inputs.



All 16 cases were recorded as \*\*NOT TESTED\*\* because the required Smart Expense Categorization API/service integration was not available for complete flow verification.



The documented integration flow is:



\*\*User â†’ HisabDo App â†’ Backend/API â†’ AI Service â†’ Model â†’ Validated Response â†’ User\*\*



Model-level evaluation does not prove that the complete application integration flow works.



\*\*Integration Testing Status:\*\* BLOCKED / NOT TESTED



\## 11. Previous Day 16 Blocker and Current Status



During Day 16, executable model evaluation was blocked because a usable trained categorization model or prediction endpoint was not available.



The current repository now contains an executable baseline experiment, and actual model-level evaluation has therefore been completed.



However, the following areas remain incomplete:



\* Full integration/API testing

\* Ambiguous input testing

\* Edge-case execution

\* Confusion matrix generation

\* Larger and more representative evaluation dataset



Therefore, the Day 16 model-availability blocker has been partially resolved at the baseline model level, while the integration-level blocker remains.



\## 12. Evaluation Limitations



The current baseline evaluation should be treated as an initial evaluation rather than final Capstone-level validation.



Key limitations include:



1\. The available labeled dataset contains only 12 records.

2\. Only 5 records were used in the test split.

3\. The small test set means that individual predictions have a large effect on the reported metrics.

4\. The current baseline uses expense description and merchant text as the combined prediction feature.

5\. Although amount preprocessing exists, the current baseline text feature does not use the amount value for prediction.

6\. A confusion matrix has not yet been generated.

7\. Ambiguous and edge-case inputs have not been executed.

8\. Full API/service integration has not been verified.



\## 13. Remaining Evaluation Work



The following work remains before final Capstone readiness:



\* \[ ] Generate and document a confusion matrix using an executable evaluation dataset.

\* \[ ] Expand the labeled dataset beyond the current small baseline sample.

\* \[ ] Execute ambiguous test cases.

\* \[ ] Execute edge-case and invalid-input tests.

\* \[ ] Execute the Day 18 integration test cases once the API/service integration is available.

\* \[ ] Record expected versus actual results for integration tests.

\* \[ ] Analyze additional incorrect predictions after expanding the evaluation set.

\* \[ ] Recalculate Accuracy, Precision, Recall, and F1-Score on a more representative test dataset.

\* \[ ] Review category-level performance and confusion patterns.

\* \[ ] Re-evaluate the model after data or feature improvements.

\* \[ ] Confirm reliable behavior before final Capstone integration.



\## 14. Blocker Summary



\*\*Current Blocker:\*\* Full Smart Expense Categorization integration testing remains blocked/not tested because the required API/service integration flow has not been verified.



\*\*Additional Evaluation Gaps:\*\*



\* Ambiguous cases not executed.

\* Edge/invalid cases not executed.

\* Confusion matrix not generated.

\* Baseline dataset is too small for final readiness assessment.



These limitations should remain visible until the corresponding tests are actually executed.



\## 15. Evidence Summary



Available evidence used for this evaluation includes:



\* Day 15 model evaluation and testing plan.

\* Day 16 model evaluation and edge-case testing document.

\* Current baseline experiment execution output.

\* Actual baseline test predictions.

\* Smart Expense Categorization sample payload definitions.

\* Day 18 integration test cases and documented blocker status.



\## 16. Overall Evaluation Status



\*\*Model-Level Baseline Evaluation:\*\* COMPLETED



\*\*Baseline Accuracy:\*\* 80%



\*\*Known Failure Cases:\*\* 1 actual incorrect prediction identified in the 5-record test set.



\*\*Confusion Matrix:\*\* NOT AVAILABLE



\*\*Ambiguous Testing:\*\* NOT TESTED



\*\*Edge-Case Testing:\*\* NOT TESTED



\*\*Integration Testing:\*\* BLOCKED / NOT TESTED



\*\*Overall Capstone Readiness:\*\* IN PROGRESS



The current baseline provides an initial measurable evaluation and identifies a healthcare-to-food classification failure. However, the available evidence is not sufficient to consider the Smart Expense Categorization model fully validated for final Capstone readiness. Additional dataset coverage, confusion-matrix analysis, ambiguous/edge-case execution, and end-to-end integration testing are still required.



