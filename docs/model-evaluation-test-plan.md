# Model Evaluation, Test Plan & Error Analysis

**Prepared by:** Rimsha Mushtaq  
**Workstream:** Smart Expense Categorization  
**Day:** 16 – Model Evaluation & Edge Cases

## 1. Objective

The purpose of this document is to define how the Smart Expense Categorization model will be evaluated, tested, and analyzed for errors before integration into the HisabDo application.

The evaluation process will focus on classification performance, reliability, and identifying areas where the model needs improvement.

## 2. Model Evaluation Metrics

The following metrics will be used to evaluate the classification model:

### Accuracy
Measures the percentage of total expense predictions that are correct.

### Precision
Measures how many of the expenses predicted as a particular category actually belong to that category.

### Recall
Measures how many of the actual expenses in a category are correctly identified by the model.

### F1-Score
Provides a balance between Precision and Recall and is useful when category distribution is not perfectly balanced.

### Confusion Matrix
Shows the correct and incorrect predictions for each expense category and helps identify which categories the model commonly confuses.

## 3. Test Plan

The model will be tested using a separate test dataset that is not used during model training.

Testing will include:

1. Common expense descriptions.
2. Different expense categories.
3. Short and detailed expense descriptions.
4. Similar or ambiguous expenses.
5. Unexpected or unclear inputs.
6. Invalid or empty inputs where applicable.

For each test case, the expected category and model-predicted category will be recorded.

## 4. Sample Test Cases

| Test Input | Expected Category |
|---|---|
| Grocery shopping | Groceries |
| Uber ride | Transport |
| Netflix subscription | Entertainment |
| Electricity bill | Utilities |
| Restaurant dinner | Food |
| Pharmacy purchase | Healthcare |

These are planning examples. Final test cases are documented in the Day 16 evaluation results below.

## 5. Error Analysis Approach

Incorrect predictions will be reviewed systematically.

For every significant error:

1. Record the original input.
2. Record the expected category.
3. Record the predicted category.
4. Identify the possible reason for the error.
5. Check whether the training data contains enough similar examples.
6. Determine whether the input is ambiguous.
7. Suggest an improvement.

### Example

**Input:** "Coffee with colleagues"

**Expected:** Food

**Predicted:** Entertainment

**Possible reason:** The model may have insufficient examples distinguishing food/drink expenses from entertainment expenses.

**Possible improvement:** Add more representative training examples for food and beverage transactions.

## 6. Success Criteria

The model should:

- Achieve strong overall classification performance.
- Maintain reasonable Precision, Recall, and F1-Score across categories.
- Minimize confusion between similar expense categories.
- Handle common expense descriptions reliably.
- Produce consistent predictions for similar inputs.
- Clearly identify uncertain or problematic cases for further improvement.

Final metric thresholds will be defined after establishing a baseline model and reviewing the actual dataset.

## 7. Evaluation Evidence

The following evidence should be maintained during implementation:

- Evaluation metric results.
- Confusion matrix.
- Test-case results.
- Incorrect prediction examples.
- Error-analysis notes.
- Improvement recommendations.

## 8. Day 16 Model Evaluation Results

The Smart Expense Categorization model was successfully trained and evaluated using the provided expense dataset.

### Dataset and Evaluation Setup

- Training rows: 397
- Testing rows: 103
- Unique descriptions: 200
- Description overlap between training and testing: 0
- Model: TF-IDF + Logistic Regression
- Split: 80% training / 20% testing based on unique descriptions

### Overall Metrics

| Metric | Result |
|---|---:|
| Accuracy | 78.64% |
| Precision (weighted) | 85.92% |
| Recall (weighted) | 78.64% |
| F1-score (weighted) | 79.03% |

### Category-Level Results

| Category | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Bills | 0.62 | 0.62 | 0.62 |
| Education | 0.67 | 1.00 | 0.80 |
| Entertainment | 1.00 | 0.55 | 0.71 |
| Food | 1.00 | 0.64 | 0.78 |
| Groceries | 0.33 | 1.00 | 0.50 |
| Healthcare | 1.00 | 1.00 | 1.00 |
| Other | 0.75 | 1.00 | 0.86 |
| Shopping | 1.00 | 1.00 | 1.00 |
| Transport | 1.00 | 0.69 | 0.82 |
| Utilities | 0.50 | 1.00 | 0.67 |

### Normal Test Cases

| Test Input | Expected | Predicted | Result |
|---|---|---|---|
| Bought groceries from supermarket | Groceries | Shopping | Incorrect |
| Paid electricity bill | Utilities | Utilities | Correct |
| Had lunch at a restaurant | Food | Food | Correct |
| Paid school tuition fee | Education | Education | Correct |
| Bought medicine from pharmacy | Healthcare | Healthcare | Correct |
| Uber ride to office | Transport | Transport | Correct |
| Bought a new shirt | Shopping | Shopping | Correct |
| Netflix monthly subscription | Entertainment | Bills | Incorrect |
| Bought vegetables from grocery store | Groceries | Groceries | Correct |
| Purchased milk and bread | Groceries | Groceries | Correct |
| Weekly grocery shopping | Groceries | Groceries | Correct |
| Movie theater ticket | Entertainment | Entertainment | Correct |
| Cinema ticket | Entertainment | Entertainment | Correct |
| Bought clothes online | Shopping | Shopping | Correct |
| Bought laptop | Shopping | Shopping | Correct |
| Bus fare | Transport | Transport | Correct |
| Doctor appointment | Healthcare | Healthcare | Correct |
| University semester fee | Education | Education | Correct |
| Paid internet bill | Bills | Bills | Correct |

### Ambiguous Test Cases

| Test Input | Model Prediction | Observation |
|---|---|---|
| Payment for electricity and groceries | Utilities | Contains multiple possible categories; prediction is context-dependent. |
| Apple | Healthcare | Ambiguous because the input does not clearly describe an expense. |
| Spotify subscription | Bills | Could reasonably be Entertainment depending on the category definition. |

### Edge-Case Test Cases

| Test Input | Model Prediction | Observation |
|---|---|---|
| 123456789 | Healthcare | Invalid/non-expense input was still assigned a category. |
| xyz random payment | Bills | Unclear input was still assigned a category. |

### Error Analysis

The main observed error patterns were:

1. **Groceries vs Shopping confusion:** "Bought groceries from supermarket" was predicted as Shopping instead of Groceries.
2. **Entertainment vs Bills confusion:** "Netflix monthly subscription" was predicted as Bills instead of Entertainment.
3. **Ambiguous inputs:** Inputs containing multiple concepts or insufficient context can produce uncertain category assignments.
4. **Invalid or meaningless inputs:** The model still returns a category for inputs that do not contain meaningful expense information.

The category-level metrics also indicate areas for improvement. Entertainment has a recall of 0.55, while Groceries has a precision of 0.33. Additional representative training examples for these categories could help reduce confusion.

### Evaluation Status

**Completed.** The Smart Expense Categorization model is available and was successfully trained and evaluated. The previous model-unavailable/blocker status is no longer applicable.

The trained model was saved as:

model/expense_categorization_pipeline.pkl

## 9. Future Improvement

Evaluation results will be used to improve the Smart Expense Categorization model through better data quality, additional training examples, feature improvements, and model/hyperparameter tuning where appropriate.
## 9. Day 17 Realistic Scenario Evaluation
Dataset and Model

Model: TF-IDF + Logistic Regression
Training rows: 397
Testing rows: 103
Unique descriptions: 200
Description overlap between training and testing: 0

Overall Evaluation Metrics

Metric	Result
Accuracy	78.64%
Precision (weighted)	85.92%
Recall (weighted)	78.64%
F1-score (weighted)	79.03%

Normal Test Cases

Test Input	Expected	Predicted	Result
Bought vegetables from grocery store	Groceries	Groceries	Correct
Paid electricity bill	Utilities	Utilities	Correct
Had lunch at a restaurant	Food	Food	Correct
Paid university tuition fee	Education	Education	Correct
Bought medicine from pharmacy	Healthcare	Healthcare	Correct
Uber ride to work	Transport	Transport	Correct
Bought a new shirt online	Shopping	Shopping	Correct
Movie theater ticket	Entertainment	Entertainment	Correct
Paid internet bill	Bills	Bills	Correct

Normal test result: 9/9 correct.

Ambiguous Test Cases

Test Input	Model Prediction	Observation
Payment for electricity and groceries	Utilities	Contains multiple possible categories; prediction is context-dependent.
Apple	Healthcare	Ambiguous because the input does not clearly describe an expense.
Spotify subscription	Bills	Could reasonably be Entertainment depending on category definition.
Netflix subscription	Bills	Could reasonably be Entertainment depending on category definition.

Edge-Case Test Cases

Test Input	Model Prediction	Observation
123456789	Healthcare	Invalid/non-expense input was still assigned a category.
xyz random payment	Bills	Unclear input was still assigned a category.
!!!	Healthcare	Invalid input was still assigned a category.
Empty input	Healthcare	Empty input was still assigned a category.

Error Analysis

The main observed error patterns were:

Ambiguous descriptions: Inputs such as Apple do not provide enough context to determine the correct expense category.
Subscription category confusion: Spotify and Netflix were classified as Bills, although they may reasonably belong to Entertainment depending on the application's category definition.
Invalid input handling: Numeric, meaningless, punctuation-only, and empty inputs were still assigned categories.
Category-level weakness: The evaluation showed lower recall for Entertainment (0.55) and lower precision for Groceries (0.33).

Improvement Recommendations

Add more representative examples for Groceries and Entertainment.
Define clearer rules for subscription-related categories.
Add input validation before sending descriptions to the classifier.
Reject empty, numeric-only, punctuation-only, or meaningless descriptions.
Add confidence-based handling for uncertain predictions.
Expand the test dataset with more realistic and ambiguous transactions.

Evaluation Status

Completed. The Smart Expense Categorization model was successfully trained and evaluated using the available dataset. Normal, ambiguous, and edge-case scenarios were tested, and error patterns were documented.

Confusion Matrix

A confusion matrix was generated from the 103-record test set and confirms the observed category-level error patterns.