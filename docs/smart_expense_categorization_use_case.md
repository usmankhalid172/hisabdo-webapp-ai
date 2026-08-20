# Smart Expense Categorization – AI/ML Use Case

## 1. Problem Statement

HisabDo users may record expenses using descriptions, merchant names, amounts, and other transaction information.

Manually assigning categories to expenses can be time-consuming and inconsistent, especially when users have a large number of transactions.

The Smart Expense Categorization feature aims to automatically predict an appropriate expense category from available transaction information.

The initial categories used in the baseline experiment are:

- Food
- Transport
- Healthcare
- Entertainment

The baseline experiment is intended as an initial proof of concept and does not represent the final production model.

---

## 2. Proposed AI Solution

The proposed solution is an ML-based expense classification pipeline.

The initial baseline approach uses:

- Text preprocessing
- TF-IDF vectorization
- Logistic Regression classification

The baseline focuses mainly on expense descriptions and merchant names because these fields can contain useful information about the type of expense.

The solution can later be extended with additional structured features such as amount, date, payment method, currency, and user transaction history when appropriate data is available.

---

## 3. Input Data Required

The candidate input fields include:

| Input Feature | Type | Purpose |
|---|---|---|
| expense_description | Text | Main textual signal for category prediction |
| merchant | Text/Categorical | Provides merchant-related context |
| amount | Numeric | May help distinguish spending patterns |
| date | Date/Time | Can provide temporal spending patterns |
| payment_method | Categorical | Provides additional transaction context |
| currency | Categorical | Supports multi-currency transaction data |

For the current baseline experiment, the primary model input is a combination of:

- expense_description
- merchant

The amount field is validated during preprocessing but is not currently used as a model feature in the baseline text classifier.

---

## 4. Processing / Model / API

The current preprocessing component performs the following steps:

1. Clean expense descriptions.
2. Convert text to lowercase.
3. Remove unnecessary leading and trailing spaces.
4. Normalize repeated whitespace.
5. Normalize merchant names.
6. Validate transaction amounts.
7. Remove duplicate records.

The preprocessing implementation is located at:

`src/expense_categorization/preprocessing.py`

After preprocessing, the expense description and merchant name are combined into a text feature.

The text is converted into numerical features using TF-IDF.

The baseline classifier is Logistic Regression.

The current baseline experiment is implemented at:

`src/expense_categorization/baseline_experiment.py`

### Baseline Flow

```text
Expense Data
     |
     v
Data Preprocessing
     |
     v
Clean Description + Merchant
     |
     v
TF-IDF Vectorization
     |
     v
Logistic Regression
     |
     v
Predicted Expense Category