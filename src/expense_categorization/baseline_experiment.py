import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from preprocessing import prepare_expense_data


# Safe sample expense data for the baseline experiment
data = pd.DataFrame(
    {
        "expense_description": [
            "Uber trip",
            "Uber ride",
            "McDonalds meal",
            "Pizza restaurant",
            "Pharmacy medicine",
            "Doctor clinic",
            "Netflix subscription",
            "Cinema ticket",
            "Uber taxi",
            "Burger meal",
            "Medical pharmacy",
            "Netflix monthly plan"
        ],
        "merchant": [
            "Uber",
            "Uber",
            "McDonalds",
            "Pizza Hut",
            "Pharmacy",
            "Clinic",
            "Netflix",
            "Cinema",
            "Uber",
            "Burger King",
            "Pharmacy",
            "Netflix"
        ],
        "amount": [
            250,
            180,
            150,
            220,
            300,
            500,
            250,
            180,
            200,
            170,
            280,
            250
        ],
        "category": [
            "Transport",
            "Transport",
            "Food",
            "Food",
            "Healthcare",
            "Healthcare",
            "Entertainment",
            "Entertainment",
            "Transport",
            "Food",
            "Healthcare",
            "Entertainment"
        ]
    }
)


# Preprocess the expense data
data = prepare_expense_data(data)


# Combine description and merchant into one text feature
data["text"] = (
    data["expense_description"]
    + " "
    + data["merchant"]
)


# Input and target
X = data["text"]
y = data["category"]


# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.34,
    random_state=42,
    stratify=y
)


# Convert text into numerical TF-IDF features
vectorizer = TfidfVectorizer()

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)


# Train the baseline classifier
model = LogisticRegression(max_iter=1000)

model.fit(X_train_tfidf, y_train)


# Make predictions
predictions = model.predict(X_test_tfidf)


# Evaluate the baseline model
accuracy = accuracy_score(y_test, predictions)

print("Baseline Accuracy:", accuracy)
print()
print("Classification Report:")
print(classification_report(y_test, predictions))
print()
print("Test Predictions:")

for text, actual, predicted in zip(X_test, y_test, predictions):
    status = "Correct" if actual == predicted else "INCORRECT"
    print(
        f"Input: {text} | Expected: {actual} | "
        f"Predicted: {predicted} | Result: {status}"
    )