# Smart Expense Categorization — AI/ML Use Case

## 1. Problem Statement

HisabDo users may record expenses using descriptions, merchant names, amounts, and other transaction information.

Manually assigning categories to expenses can be time-consuming and inconsistent, especially when users have a large number of transactions.

The **Smart Expense Categorization** feature aims to predict an appropriate expense category automatically from the available transaction information.

The initial baseline experiment uses the following categories:

- Food
- Transport
- Healthcare
- Entertainment

> **Note:** This baseline is an initial proof of concept. It does not represent the final production model.

## 2. Proposed AI Solution

The proposed solution is a machine-learning-based expense classification pipeline.

The initial baseline approach uses:

- Text preprocessing
- TF-IDF vectorization
- Logistic Regression classification

The baseline focuses mainly on expense descriptions and merchant names because these fields can provide useful information about the type of expense.

The solution may later be extended with additional structured features, such as amount, date, payment method, currency, and user transaction history, when appropriate data is available.

## 3. Required Input Data

The candidate input fields are listed below.

| Input feature | Data type | Purpose |
|---|---|---|
| `expense_description` | Text | Provides the main textual signal for category prediction. |
| `merchant` | Text/Categorical | Provides merchant-related context. |
| `amount` | Numeric | May help distinguish spending patterns. |
| `date` | Date/Time | May provide information about temporal spending patterns. |
| `payment_method` | Categorical | Provides additional transaction context. |
| `currency` | Categorical | Supports multi-currency transaction data. |

### Features Used in the Baseline

The current baseline experiment primarily uses:

- `expense_description`
- `merchant`

The `amount` field is validated during preprocessing but is **not currently used as a model feature** in the baseline text classifier.

The other listed fields are candidate inputs for potential future extensions, not confirmed inputs to the current baseline model.

## 4. Processing and Model Pipeline

The preprocessing component performs the following steps:

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

The text is then converted into numerical features using **TF-IDF**. These features are passed to a **Logistic Regression** classifier to predict an expense category.

The baseline experiment is implemented at:

`src/expense_categorization/baseline_experiment.py`

### Baseline Workflow

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
```
