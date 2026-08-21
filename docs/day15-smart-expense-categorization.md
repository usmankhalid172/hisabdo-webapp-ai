DAY 15 — AI FEATURE PLANNING
Smart Expense Categorization
Prepared by: Mehar Ali
Department 1 — AI/ML Team
HisabDo Capstone Project

Feature: Smart Expense Categorization
Primary Goal: Define the AI feature design, model approach, input/output contract, and implementation flow.
Repository: hisabdo-webapp-ai

1. Problem Statement

HisabDo users record expenses with information such as a description, amount, and potentially a merchant or payment detail. Manually assigning a category to every expense can be repetitive and may lead to inconsistent categorization. Smart Expense Categorization will automatically predict an appropriate expense category from the available transaction information.

2. Proposed AI Solution

The proposed first-stage solution is a supervised machine-learning text classification system. The expense description is converted into numerical features using TF-IDF, and a Logistic Regression classifier predicts the most likely expense category.

Initial model pipeline:

• Expense description and transaction data are received.
• Text is cleaned and normalized.
• TF-IDF converts the expense description into numerical features.
• Logistic Regression classifies the expense into a predefined category.
• The service returns the predicted category and a confidence/probability value where supported.

3. Initial Expense Categories

For the first POC, a limited category set is recommended so the model can be trained and evaluated consistently:

Food
Groceries
Transport
Utilities
Healthcare
Shopping
Entertainment
Education
Bills
Other

4. Required Input Data

The minimum input for the initial POC should be:

Field: description
Type: String
Purpose: Main text used for category prediction.

Field: amount
Type: Number
Purpose: Transaction amount; can support future feature engineering.

Potential future inputs include merchant name, date, payment method, location, and user-specific historical behavior. These should be added only after the basic POC is validated.

5. Input / Output Contract

Example Request:

{
"description": "Bought groceries from Imtiaz",
"amount": 3500
}

Example Response:

{
"category": "Groceries",
"confidence": 0.91
}

The exact confidence representation will be finalized during the implementation/API stage. If confidence is not considered reliable enough for production use, the service should return the category without exposing a misleading confidence score.

6. Proposed Architecture

High-level flow:

HisabDo Application
↓
HisabDo Backend / API
↓
Smart Expense Categorization Service
↓
Input Validation & Preprocessing
↓
TF-IDF Vectorizer
↓
Logistic Regression Model
↓
Predicted Category + Confidence
↓
Validated API Response
↓
HisabDo Application

7. Model Approach

Component: Text preprocessing
Selected Approach: Basic cleaning / normalization
Reason: Reduces noise in expense descriptions.

Component: Feature extraction
Selected Approach: TF-IDF
Reason: Simple, fast, interpretable text representation.

Component: Classifier
Selected Approach: Logistic Regression
Reason: Good baseline for multi-class text classification.

Component: Evaluation
Selected Approach: Accuracy, Precision, Recall, F1-score
Reason: Measures overall and per-category performance.

This is a baseline POC rather than a final production model. More advanced approaches can be evaluated later if the baseline does not meet the required performance.

8. Example Predictions

Sample Expense: Bought milk from Imtiaz
Expected Category: Groceries
Purpose: Normal grocery transaction.

Sample Expense: Petrol from PSO
Expected Category: Transport
Purpose: Fuel/transport example.

Sample Expense: Electricity bill payment
Expected Category: Utilities
Purpose: Utility payment.

Sample Expense: Restaurant dinner
Expected Category: Food
Purpose: Food transaction.

Sample Expense: Bought medicine from pharmacy
Expected Category: Healthcare
Purpose: Healthcare transaction.

Sample Expense: Bought a pair of shoes
Expected Category: Shopping
Purpose: Retail shopping.

9. Dataset Requirements

• Each training record should contain an expense description and a category label.
• The dataset should contain multiple examples for every category.
• Training examples should include different wording for similar expenses.
• Duplicate or contradictory records should be reviewed during cleaning.
• The dataset should be split into training and testing portions before final evaluation.
• Real user financial data should not be added without appropriate authorization, privacy protection, and anonymization.

10. Testing and Evaluation Plan

The POC should be tested using both standard metrics and realistic expense examples.

• Accuracy — overall percentage of correctly classified expenses.
• Precision — how often predicted categories are correct.
• Recall — how many actual examples of a category are correctly identified.
• F1-score — balance between precision and recall.
• Confusion matrix — identify categories that the model commonly confuses.
• Edge-case testing — short descriptions, spelling variations, unknown merchants, ambiguous expenses, and incomplete descriptions.

11. Risks and Limitations

• A small or unbalanced dataset can produce unreliable predictions.
• Ambiguous descriptions may belong to multiple reasonable categories.
• New merchants or uncommon wording may reduce prediction quality.
• The baseline model may require retraining as more real expense data becomes available.
• Confidence scores should not be treated as guaranteed correctness.
• Financial data requires careful privacy and security handling.
