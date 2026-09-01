import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

ROOT = Path(__file__).resolve().parents[2]

# Load dataset
df = pd.read_csv(ROOT / "data" / "expense_data.csv")

# Convert columns to string
df["description"] = df["description"].astype(str)
df["category"] = df["category"].astype(str)

# Get unique descriptions
unique_descriptions = df["description"].unique()

# Split unique descriptions first
train_descriptions, test_descriptions = train_test_split(
    unique_descriptions,
    test_size=0.20,
    random_state=42
)

# Create train/test datasets using the unique descriptions
train_df = df[df["description"].isin(train_descriptions)]
test_df = df[df["description"].isin(test_descriptions)]

X_train = train_df["description"]
y_train = train_df["category"]

X_test = test_df["description"]
y_test = test_df["category"]

# Verify that no description exists in both sets
overlap = set(X_train).intersection(set(X_test))

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Unique descriptions:", len(unique_descriptions))
print("Description overlap:", len(overlap))

# Create ML pipeline
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2)
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000,
            random_state=42
        )
    )
])

# Train model
model.fit(X_train, y_train)

# Make predictions
pred = model.predict(X_test)

# Get prediction confidence
probabilities = model.predict_proba(X_test)
confidence = probabilities.max(axis=1)

# Set confidence threshold
CONFIDENCE_THRESHOLD = 0.30

# Apply "Needs Review" fallback to low-confidence predictions
pred_with_review = pred.copy()
pred_with_review[confidence < CONFIDENCE_THRESHOLD] = "Needs Review"

# Evaluation metrics

# Evaluation metrics
accuracy = accuracy_score(y_test, pred)
precision = precision_score(y_test, pred, average="weighted", zero_division=0)
recall = recall_score(y_test, pred, average="weighted", zero_division=0)
f1 = f1_score(y_test, pred, average="weighted", zero_division=0)

print("\nEvaluation Results")
print("------------------")
print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1-score:", f1)

print("\nClassification Report")
print("---------------------")
print(classification_report(y_test, pred, zero_division=0))

# Evaluate confidence-based workflow
accepted_mask = confidence >= CONFIDENCE_THRESHOLD

if accepted_mask.any():
    accepted_accuracy = accuracy_score(
        y_test[accepted_mask],
        pred[accepted_mask]
    )
else:
    accepted_accuracy = 0.0

coverage = accepted_mask.mean()

print("\nConfidence-Based Evaluation")
print("---------------------------")
print("Confidence threshold:", CONFIDENCE_THRESHOLD)
print("Accepted predictions:", accepted_mask.sum())
print("Needs Review:", (~accepted_mask).sum())
print("Coverage:", coverage)
print("Accuracy on accepted predictions:", accepted_accuracy)

# Create model output directory if it does not exist
model_dir = ROOT / "model"
model_dir.mkdir(parents=True, exist_ok=True)

# Save model locally
model_path = model_dir / "expense_categorization_pipeline.pkl"
joblib.dump(model, model_path)

print("\nSaved model to:", model_path)