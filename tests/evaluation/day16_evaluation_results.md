# AI/ML Evaluation Results - Day 16

## Ownership

**Prepared by:** Syeda Isma Nazir  
**Responsibility:** Testing / Validation  
**Project:** HisabDo AI/ML Capstone  
**Day:** 16

---

## Model Validation

**Feature:** Smart Expense Categorization

**Validation Environment:**
- Python 3.14.6
- pandas
- scikit-learn
- joblib

**Validation Method:** Model training and evaluation using the corrected expense categorization evaluation setup.

The corrected evaluation splits **unique expense descriptions first** and then creates the training and testing datasets. This prevents identical descriptions from appearing in both sets.

### Result

| Metric | Result |
|---|---:|
| Accuracy | **78.64%** |
| Precision | **85.92%** |
| Recall | **78.64%** |
| F1-Score | **79.03%** |
| Training Samples | **397** |
| Test Samples | **103** |
| Unique Descriptions | **200** |
| Description Overlap | **0** |

**Status:** PASS

### Category-Level Results

| Category | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| Bills | 0.62 | 0.62 | 0.62 | 13 |
| Education | 0.67 | 1.00 | 0.80 | 8 |
| Entertainment | 1.00 | 0.55 | 0.71 | 20 |
| Food | 1.00 | 0.64 | 0.78 | 11 |
| Groceries | 0.33 | 1.00 | 0.50 | 2 |
| Healthcare | 1.00 | 1.00 | 1.00 | 9 |
| Other | 0.75 | 1.00 | 0.86 | 12 |
| Shopping | 1.00 | 1.00 | 1.00 | 10 |
| Transport | 1.00 | 0.69 | 0.82 | 13 |
| Utilities | 0.50 | 1.00 | 0.67 | 5 |

### Evaluation Evidence

The corrected model training and evaluation script was executed successfully with:

```text
python src\expense_categorization\train_model.py