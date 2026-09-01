# Day 20 – Data Preprocessing & Baseline Model Validation

## 1. Work Completed

* Validated the existing expense preprocessing pipeline in `src/expense_categorization/preprocessing.py`.
* Validated the existing baseline experiment in `src/expense_categorization/baseline_experiment.py`.
* Verified the saved categorization model at `model/expense_categorization_pipeline.pkl`.
* Validated sample expense inputs and preprocessing behavior.
* Tested the baseline model and recorded evaluation metrics.
* Tested the saved model with representative expense descriptions.
* Checked compatibility between sample API payload fields and the trained model input.

## 2. Preprocessing Validation

The preprocessing pipeline was tested for text cleaning, merchant normalization, amount validation, and duplicate removal.

### Validation Results

| Test case                           | Result                                                             |
| ----------------------------------- | ------------------------------------------------------------------ |
| Extra spaces in expense description | Passed – normalized to lowercase and single spaces                 |
| Merchant name normalization         | Passed                                                             |
| Negative amount                     | Converted to invalid/NaN value                                     |
| Invalid amount type                 | Converted to invalid/NaN value                                     |
| Duplicate record                    | Removed                                                            |
| Empty expense description           | Gap identified – empty value is retained instead of being rejected |

### Example

Input:

`" Uber   trip "` → `uber trip`

Input:

`" Uber "` → `uber`

Negative amount:

`-100` → `NaN`

Invalid amount:

`"invalid"` → `NaN`

## 3. Baseline Experiment

The existing baseline experiment uses:

* TF-IDF text vectorization
* Logistic Regression classifier
* Combined expense description and merchant text

### Baseline Results

| Metric             | Result |
| ------------------ | -----: |
| Accuracy           |   0.80 |
| Weighted Precision |   0.90 |
| Weighted Recall    |   0.80 |
| Weighted F1-score  |   0.80 |

The baseline experiment completed successfully.

### Observed Error Areas

* Food precision: 0.50
* Healthcare recall: 0.50

These results indicate that the small baseline sample contains some category confusion and should not be treated as a final production performance measurement.

## 4. Saved Model Validation

The saved model was confirmed as a scikit-learn pipeline containing:

* TF-IDF Vectorizer
* Logistic Regression

Representative predictions:

| Input                        | Predicted Category |
| ---------------------------- | ------------------ |
| Uber trip                    | Transport          |
| Pizza restaurant             | Food               |
| Pharmacy medicine            | Healthcare         |
| Netflix monthly subscription | Bills              |
| university tuition this week | Education          |

### Observed Category Inconsistency

`Netflix monthly subscription` was predicted as `Bills`.

The sample baseline data/payloads associate Netflix with `Entertainment`.

This indicates a category-label inconsistency that should be reviewed before final model integration.

## 5. API Input Compatibility Validation

The sample API payload contains:

* `expense_description`
* `merchant`
* `amount`
* `currency`
* `payment_method`

However, the currently trained production model in `train_model.py` is trained using the `description` field only.

Therefore:

* API payload fields are not fully aligned with the trained model input.
* `merchant`, `amount`, `currency`, and `payment_method` are not currently used by the trained model.
* A mapping from `expense_description` to the model's `description` input is required for compatibility.
* Any future decision to use additional fields will require model retraining and pipeline changes.

## 6. Validation Examples Reviewed

The existing sample payload file contains cases for:

* Missing description
* Negative amount
* Missing merchant
* Invalid amount type

The preprocessing code handles invalid numeric amounts, but empty descriptions are not currently rejected.

## 7. Current Dependency / Blocker

The main dependency is alignment between:

1. The API request schema,
2. preprocessing output,
3. the trained model input schema, and
4. the category labels used across datasets/sample payloads.

The trained categorization model and dataset are available, but final integration should confirm the expected input field mapping and category-label consistency.

## 8. Recommended Next Steps

1. Add explicit validation for empty/blank expense descriptions if the API requires a valid description.
2. Confirm whether `expense_description` should map directly to the model's `description` field.
3. Confirm the intended category for subscription expenses such as Netflix.
4. Keep additional payload fields only if they are intentionally supported by the model/API contract.
5. Re-run evaluation on a larger and representative validation dataset before treating the baseline result as production performance.

## 9. Evidence

* Feature branch: `feature/rimsha-mushtaq-data-preprocessing-day-20`
* Preprocessing code: `src/expense_categorization/preprocessing.py`
* Baseline experiment: `src/expense_categorization/baseline_experiment.py`
* Training/model pipeline: `src/expense_categorization/train_model.py`
* Dataset: `data/expense_data.csv`
* Sample payloads: `data/expense_category_sample_payloads.json`
* Saved model: `model/expense_categorization_pipeline.pkl`

## 10. Status

**Status: Validation completed; integration alignment and input/category consistency require confirmation before final completion.**
git status