# Day 17 — Smart Expense Categorization Realistic Use Cases

**Prepared by:** Mehar Ali
**Workstream:** AI / ML — Smart Expense Categorization
**Day:** 17
**Repository:** hisabdo-webapp-ai

## 1. Objective

The objective of Day 17 was to apply the existing Smart Expense Categorization POC to realistic HisabDo transaction descriptions.

The testing focused on:

* Testing realistic transaction descriptions across different expense categories.
* Confirming model input and output.
* Recording correct and incorrect predictions.
* Identifying ambiguous and low-confidence predictions.
* Identifying current model limitations.

## 2. Model Input and Output

The current model uses the transaction **description** as its input.

Example:

`KFC dinner`

The dataset also contains an `amount` field, but the current model does not use the amount for prediction.

The model uses:

**Transaction Description → TF-IDF → Logistic Regression → Predicted Category**

The prediction code also reports the highest class probability as the prediction confidence.

## 3. Realistic HisabDo Use Cases

| #  | Transaction Description         | Expected Category | Predicted Category | Confidence | Result    |
| -- | ------------------------------- | ----------------- | ------------------ | ---------: | --------- |
| 1  | KFC dinner                      | Food              | Food               |       0.33 | Correct   |
| 2  | McDonald's lunch                | Food              | Food               |       0.25 | Correct   |
| 3  | Bought groceries from Imtiaz    | Groceries         | Shopping           |       0.44 | Incorrect |
| 4  | Milk and bread from supermarket | Groceries         | Groceries          |       0.41 | Correct   |
| 5  | Uber ride to university         | Transport         | Transport          |       0.46 | Correct   |
| 6  | Petrol from PSO                 | Transport         | Transport          |       0.37 | Correct   |
| 7  | Electricity bill payment        | Utilities         | Utilities          |       0.74 | Correct   |
| 8  | Gas bill payment                | Utilities         | Utilities          |       0.62 | Correct   |
| 9  | Pharmacy medicine               | Healthcare        | Healthcare         |       0.48 | Correct   |
| 10 | Doctor consultation fee         | Healthcare        | Healthcare         |       0.57 | Correct   |
| 11 | Bought shoes from shopping mall | Shopping          | Groceries          |       0.33 | Incorrect |
| 12 | Daraz shopping order            | Shopping          | Groceries          |       0.30 | Incorrect |
| 13 | Netflix subscription            | Entertainment     | Bills              |       0.33 | Incorrect |
| 14 | Cinema movie ticket             | Entertainment     | Entertainment      |       0.54 | Correct   |
| 15 | University tuition fee          | Education         | Education          |       0.61 | Correct   |
| 16 | Bought programming book         | Education         | Groceries          |       0.23 | Incorrect |
| 17 | Internet bill payment           | Bills             | Bills              |       0.64 | Correct   |
| 18 | Mobile phone bill               | Bills             | Bills              |       0.48 | Correct   |
| 19 | Miscellaneous expense           | Other             | Other              |       0.49 | Correct   |
| 20 | General household expense       | Other             | Other              |       0.65 | Correct   |

## 4. Test Summary

* Total transactions tested: **20**
* Correct predictions: **15**
* Incorrect predictions: **5**
* Realistic use-case accuracy: **75%**

## 5. Correct Predictions

The model correctly handled common transaction descriptions such as:

* KFC dinner → Food
* Uber ride → Transport
* Petrol from PSO → Transport
* Electricity bill payment → Utilities
* Gas bill payment → Utilities
* Pharmacy medicine → Healthcare
* Cinema movie ticket → Entertainment
* University tuition fee → Education
* Internet bill payment → Bills

These results show that the baseline model can recognize several common expense patterns.

## 6. Incorrect Predictions

### Bought groceries from Imtiaz

**Expected:** Groceries
**Predicted:** Shopping
**Confidence:** 0.44

The merchant name and general shopping context may have caused confusion between Groceries and Shopping.

### Bought shoes from shopping mall

**Expected:** Shopping
**Predicted:** Groceries
**Confidence:** 0.33

The model may not contain enough representative footwear or clothing examples.

### Daraz shopping order

**Expected:** Shopping
**Predicted:** Groceries
**Confidence:** 0.30

Daraz is a general marketplace, so the merchant name alone does not identify the actual expense category.

### Netflix subscription

**Expected:** Entertainment
**Predicted:** Bills
**Confidence:** 0.33

The word "subscription" may have caused the model to associate the transaction with recurring bills.

### Bought programming book

**Expected:** Education
**Predicted:** Groceries
**Confidence:** 0.23

The model may have insufficient examples related to books and educational purchases.

## 7. Ambiguous / Low-Confidence Cases

Some predictions had relatively low confidence:

* McDonald's lunch → Food: **0.25**
* Bought programming book → Groceries: **0.23**
* KFC dinner → Food: **0.33**
* Daraz shopping order → Groceries: **0.30**
* Netflix subscription → Bills: **0.33**

These cases show that the model's confidence should not be treated as guaranteed correctness.

## 8. Current Model Limitations

The Day 17 testing identified these limitations:

1. The model can struggle with merchants that are not sufficiently represented in the training data.
2. General marketplace names such as Daraz do not always provide enough category information.
3. Similar categories such as Shopping and Groceries can be confused.
4. Subscription-based expenses can be confused with Bills.
5. The current model uses only the transaction description; the amount is not currently used.
6. New wording, merchants, and uncommon transaction descriptions may reduce prediction quality.
7. The baseline TF-IDF + Logistic Regression model requires more representative training data before production use.

## 9. Recommended Improvements

Future improvements include:

* Add more examples for frequently confused categories.
* Add local merchant examples.
* Include merchant information as an additional feature.
* Evaluate whether transaction amount can improve classification.
* Add Roman Urdu and spelling variations.
* Add more Pakistani/local transaction descriptions.
* Use confidence-based review for uncertain predictions.
* Retrain the model as more representative data becomes available.

## 10. Blocker / Confusion Note

At the beginning of Day 17, the existing model artifact was incompatible with the current scikit-learn environment.

The previous model was created using scikit-learn 1.5.2 while the current environment uses scikit-learn 1.7.2. Loading the old model produced a version warning and Pipeline compatibility error.

The model was regenerated using scikit-learn 1.7.2 and then loaded successfully.

After resolving this issue, realistic transaction testing was completed successfully.

## 11. Evidence

Prediction code:

`src/expense_categorization/predict_transactions.py`

Existing trained model:(Saved Locally)

`model/expense_categorization_pipeline.pkl`

Training dataset:

`data/expense_data.csv`

Execution command:

`python src/expense_categorization/predict_transactions.py`

Observed result:

**15/20 correct — 75% realistic transaction test accuracy**

## 12. Conclusion

The Day 17 testing shows that the Smart Expense Categorization POC can correctly classify many common HisabDo transaction descriptions.

However, the incorrect predictions demonstrate limitations around merchant context, ambiguous wording, and insufficient training examples.

The current POC is suitable for continued experimentation and improvement but should not yet be considered production-ready.
