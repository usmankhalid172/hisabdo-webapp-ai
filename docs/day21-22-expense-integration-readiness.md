# Day 21–22 – Expense Categorization Integration Readiness

## Objective

Move the existing Smart Expense Categorization POC toward integration readiness without creating a new classifier.

The existing TF-IDF + Logistic Regression model is wrapped with an integration-readiness layer that validates inputs, returns predicted categories, exposes confidence, and applies a configurable confidence threshold.

## Existing Model

The existing model is trained using:

- TF-IDF Vectorizer
- Lowercase text processing
- English stop-word removal
- Unigrams and bigrams
- Logistic Regression classifier

The trained model is stored as:

`model/expense_categorization_pipeline.pkl`

No new classifier was created for Day 21–22.

## Integration Flow

```text
Expense Description
        |
        v
Input Validation
        |
        v
Existing Expense Categorization Model
        |
        +------------------+
        |                  |
        v                  v
   Predicted Category   Confidence
        |                  |
        +--------+---------+
                 |
                 v
        Confidence Threshold
                 |
          +------+------+
          |             |
       Accepted       Rejected


Integration Component

Implementation:

src/expense_categorization/integration_readiness.py

The integration layer provides:

Description validation
Model loading
Category prediction
Probability-based confidence
Configurable confidence threshold
Accepted/rejected decision
Input Contract

The integration layer expects a non-empty string.

Example:

{
  "description": "Uber ride to university"
}

Invalid inputs include:

Empty string
Whitespace-only string
Non-string values
None
Output Contract

Example:

{
  "category": "Transport",
  "confidence": 0.46345802888754367,
  "accepted": false
}
Output fields
Field	Type	Description
category	string	Predicted expense category
confidence	float	Maximum model probability between 0 and 1
accepted	boolean	Whether confidence meets the configured threshold
Confidence Handling

The default confidence threshold is:

0.50

A prediction is accepted when:

confidence >= 0.50

Otherwise, the prediction is marked as not accepted.

The threshold is configurable so that the consuming application can adjust the trade-off between coverage and confidence.

Sample Prediction

Input:

Uber ride to university

Actual model result:

Category: Transport
Confidence: 0.46345802888754367
Accepted: False

Although the predicted category is correct for this test case, the confidence is below the default integration threshold. This demonstrates why the application should not treat every model prediction as equally reliable.

Integration Evaluation

Evaluation input:

data/day21_integration_test_cases.csv

Evaluation output:

data/day21_integration_results.csv

The evaluation contained:

12 total cases
10 cases with expected categories
2 edge cases without expected categories

Results:

Metric	Result
Total cases	12
Labeled cases	10
Correct predictions	8
Integration test accuracy	80.00%
Average confidence	41.57%
Accepted predictions at 0.50	2/10
Representative Results
Description	Expected	Predicted	Confidence	Accepted	Correct
KFC dinner	Food	Food	33.27%	No	Yes
Uber ride to university	Transport	Transport	46.35%	No	Yes
Electricity bill payment	Utilities	Utilities	74.11%	Yes	Yes
Pharmacy medicine	Healthcare	Healthcare	47.96%	No	Yes
Bought groceries from Imtiaz	Groceries	Shopping	44.10%	No	No
Netflix monthly subscription	Bills	Bills	25.85%	No	Yes
New laptop purchase	Shopping	Other	24.99%	No	No
University tuition payment	Education	Education	42.47%	No	Yes
Concert ticket	Entertainment	Entertainment	55.52%	Yes	Yes
Random xyz qwerty	Other	Other	21.04%	No	Yes
Confidence Threshold Analysis

The same labeled evaluation set was used to compare thresholds.

Threshold	Accepted	Correct Accepted	Incorrect Accepted	Accepted Accuracy
0.30	7	6	1	85.71%
0.40	6	5	1	83.33%
0.50	2	2	0	100.00%
0.60	1	1	0	100.00%
0.70	1	1	0	100.00%
Threshold Recommendation

A threshold of 0.50 is retained as the initial conservative integration threshold.

On this small evaluation set, all predictions accepted at 0.50 were correct.

However, this should not be interpreted as production-level 100% accuracy because the evaluation contains only 10 labeled examples.

A larger validation dataset should be used before establishing a production threshold.

Edge Cases

The integration layer handles:

Empty description
""

Result:

ValueError: Description cannot be empty.
Whitespace-only description
"   "

Result:

ValueError: Description cannot be empty.
Invalid input type

Examples:

None
12345
["Uber ride"]
{"description": "Uber ride"}

Result:

ValueError: Description must be a string.
Missing model

If the model artifact is unavailable, initialization raises a FileNotFoundError.

Invalid confidence threshold

Thresholds below 0.0 or above 1.0 are rejected.

Automated Tests

Test file:

tests/test_integration_readiness.py

The integration test suite contains:

Valid prediction test
Expected-category tests
Confidence threshold acceptance test
High-threshold rejection test
Empty input tests
Non-string input tests
Invalid threshold tests
Missing model test

Test result:

13 passed
Evaluation Scripts

Integration evaluation:

scripts/day21_evaluate_integration.py

Confidence threshold analysis:

scripts/day21_threshold_analysis.py

Integration Requirements

The Capstone application should provide:

Input
description: string

The description should be non-empty.

Output
category: string
confidence: float
accepted: boolean
Consumer Behavior

The consuming application can:

Automatically accept high-confidence predictions.
Flag low-confidence predictions for user confirmation.
Store the category and confidence for later analysis.
Use user corrections as future training/evaluation data.
Known Limitations
The current dataset is relatively small.
The evaluation sample contains only 10 labeled integration cases.
Some realistic merchant descriptions are misclassified.
Correct predictions can still have low confidence.
Confidence is model probability, not a guarantee of correctness.
The existing classifier's category vocabulary remains unchanged.
The 0.50 threshold is an initial integration threshold and requires validation on a larger dataset.
Capstone Integration Recommendation

The current Smart Expense Categorization POC is ready for controlled backend integration testing.

The recommended integration behavior is:

High-confidence prediction
        |
        v
Automatically accept category

Low-confidence prediction
        |
        v
Ask user for confirmation
or flag for review

The model itself does not need to be replaced for this integration stage.

Future work should focus on:

Larger and more representative evaluation data.
Threshold tuning using validation data.
Monitoring incorrect and low-confidence predictions.
Capturing user corrections.
Integration with the Capstone backend/API.
