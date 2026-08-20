# Smart Expense Categorization – AI/ML Planning Note

## 1. Objective

The Smart Expense Categorization feature aims to automatically predict a category for an expense based on the information available in the expense record.

Examples of expense categories may include:

- Food
- Transport
- Shopping
- Bills & Utilities
- Healthcare
- Entertainment
- Education
- Other

The purpose of this document is to define the initial data preprocessing requirements, candidate input features, and a simple baseline machine-learning approach.

---

## 2. Data Preprocessing Requirements

Before training a machine-learning model, expense data should be cleaned and transformed into a consistent format.

### 2.1 Missing Values

- Check important fields for missing values.
- If `expense_description` is missing, use another available field such as `merchant` when possible.
- Handle missing numerical values such as `amount` using an appropriate strategy when required.
- Avoid creating artificial text values that could mislead the text-classification model.

### 2.2 Expense Description Cleaning

Text fields such as `expense_description` should be normalized before model training.

Recommended preprocessing includes:

- Convert text to a consistent case.
- Remove unnecessary whitespace.
- Normalize common formatting variations.
- Remove irrelevant characters where appropriate.
- Handle empty or very short descriptions.
- Preserve meaningful words because they may be important for category prediction.

Example:

```text
"  McDONALDS #123  "
```

can be normalized to:

```text
"mcdonalds #123"
```

### 2.3 Merchant Normalization

Merchant names may appear in different forms.

For example:

```text
Uber *Trip
UBER TRIP
Uber Technologies
```

may refer to the same merchant or service.

Merchant names should therefore be normalized where possible to reduce unnecessary variations.

### 2.4 Amount Validation

The `amount` field should be validated before use.

The preprocessing stage should:

- Ensure that the amount is numeric.
- Check for missing values.
- Check for invalid or unexpected negative values.
- Identify zero or unrealistic amounts.
- Investigate extreme values before model training.

Valid transaction amounts should be preserved.

### 2.5 Category Standardization

Target category labels must use a consistent vocabulary.

For example:

```text
Food
food
FOOD
```

should be standardized to one label such as:

```text
Food
```

Duplicate or conflicting category names should be reviewed before training.

### 2.6 Duplicate Records

Accidental duplicate expense records should be identified and removed when appropriate.

This helps prevent duplicated examples from biasing the training process.

### 2.7 Date Processing

If transaction dates are available, useful derived features can be created, such as:

- Day of week
- Month
- Day of month
- Weekend indicator

The raw date should not be passed directly into a simple machine-learning model without preprocessing.

### 2.8 Text Vectorization

Machine-learning models cannot directly process raw text.

For the initial text-classification baseline, expense descriptions should be converted into numerical features using:

**TF-IDF (Term Frequency–Inverse Document Frequency).**

---

## 3. Candidate Input Features

The following features are potential inputs for the Smart Expense Categorization model:

| Feature | Type | Purpose |
|---|---|---|
| `expense_description` | Text | Main signal for predicting the expense category |
| `merchant` | Text/Categorical | Helps identify merchant-specific spending patterns |
| `amount` | Numeric | May help distinguish different spending types |
| `payment_method` | Categorical | Provides additional transaction context |
| `currency` | Categorical | Useful when multiple currencies are supported |
| `date` | Date | Can be transformed into useful time-related features |
| `day_of_week` | Derived | May capture weekly spending patterns |
| `month` | Derived | May capture seasonal spending patterns |
| `is_weekend` | Boolean | Provides behavioral context |
| `user_category_history` | Historical/Optional | Can improve predictions if reliable user history is available |

### Recommended Initial Features

For the first baseline implementation, the recommended primary features are:

1. `expense_description`
2. `merchant`

Additional structured features such as:

- `amount`
- `payment_method`
- `currency`
- date-derived features

can be evaluated after the initial text-based baseline is established.

---

## 4. Baseline Model Approach

### Recommended Baseline

The proposed initial baseline model is:

**TF-IDF + Logistic Regression**

This approach is simple, fast, interpretable, and suitable for establishing a benchmark for text-based multiclass classification.

### Proposed Pipeline

```text
Expense Data
     |
     v
Data Validation
     |
     v
Text Cleaning
     |
     v
Prepare Description + Merchant
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

### 4.1 TF-IDF

TF-IDF converts text into numerical features based on the importance of words in the dataset.

For example, words or tokens such as:

- `uber`
- `restaurant`
- `pharmacy`
- `electricity`
- `cinema`

may provide useful signals for predicting expense categories.

### 4.2 Logistic Regression

Logistic Regression can be used as a multiclass classification model to predict the expense category from the TF-IDF features.

It is a suitable baseline because it is:

- Simple to implement
- Fast to train
- Easy to evaluate
- Easy to interpret
- Effective for many sparse text-classification tasks

---

## 5. Training and Evaluation Plan

The labeled dataset should be divided into training and evaluation data.

Recommended initial split:

- 80% training data
- 20% test data

If the dataset is large enough, a separate validation set or cross-validation can be used during model selection.

### Evaluation Metrics

The baseline model should be evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix

For imbalanced expense categories, **macro F1-score** should receive particular attention because it gives equal importance to each category.

---

## 6. Data Leakage Considerations

Preprocessing and vectorization steps must be fitted only on the training data.

For example, the TF-IDF vocabulary and statistics should be learned from the training set and then applied to validation and test data.

This prevents information from the test set from leaking into model training and producing overly optimistic evaluation results.

---

## 7. Initial Assumptions

The initial approach assumes that:

- Training expenses have known category labels.
- Expense descriptions and/or merchant names are available for a reasonable portion of records.
- Category labels are standardized.
- The first version uses supervised classification.
- The baseline is intended to provide a measurable starting point rather than represent the final production model.

---

## 8. Example Prediction

For a new expense such as:

```text
Description: Uber trip
Merchant: Uber
Amount: 250
```

the model may return:

```text
Predicted Category: Transport
```

The exact prediction will depend on the training dataset and learned model parameters.

---

## 9. Future Improvements

After establishing and evaluating the baseline, the team can consider:

- Combining text with structured numerical and categorical features.
- Class-balancing techniques for underrepresented categories.
- Hyperparameter tuning.
- Alternative classifiers such as Linear SVM.
- More advanced NLP embeddings.
- Transformer-based text classification if justified by the dataset size and requirements.
- User-specific spending history.
- Confidence scores for predictions.
- Fallback handling for low-confidence predictions.

---

## 10. Responsibility and Scope

My responsibility in the Smart Expense Categorization workstream is to define:

1. Expense-data preprocessing requirements.
2. Candidate input features.
3. A simple baseline-model approach.
4. Initial evaluation considerations.
5. Data-quality and data-leakage considerations.

This planning note provides the initial AI/ML design for the Smart Expense Categorization feature and serves as a starting point for the later implementation and integration phases.