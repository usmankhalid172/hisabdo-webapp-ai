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

**Validation Method:** Model training and evaluation using the available expense categorization dataset.

### Result

**Accuracy:** 1.00 (100%)

| Category | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| Bills | 1.00 | 1.00 | 1.00 | 10 |
| Education | 1.00 | 1.00 | 1.00 | 10 |
| Entertainment | 1.00 | 1.00 | 1.00 | 10 |
| Food | 1.00 | 1.00 | 1.00 | 10 |
| Groceries | 1.00 | 1.00 | 1.00 | 10 |
| Healthcare | 1.00 | 1.00 | 1.00 | 10 |
| Other | 1.00 | 1.00 | 1.00 | 10 |
| Shopping | 1.00 | 1.00 | 1.00 | 10 |
| Transport | 1.00 | 1.00 | 1.00 | 10 |
| Utilities | 1.00 | 1.00 | 1.00 | 10 |

**Test Samples:** 100

**Status:** PASS

### Evidence

The model training and evaluation script was executed successfully with:

```text
python src\expense_categorization\train_model.py
```