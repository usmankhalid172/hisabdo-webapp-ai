import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

ROOT = Path(__file__).resolve().parents[2]

df = pd.read_csv(ROOT / "data" / "expense_data.csv")

X, y = df["description"].astype(str), df["category"].astype(str)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

model = Pipeline([
    ("tfidf", TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2))),
    ("classifier", LogisticRegression(max_iter=1000, random_state=42))
])

model.fit(X_train, y_train)
pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, pred))
print(classification_report(y_test, pred, zero_division=0))

# Create model output directory if it does not exist
model_dir = ROOT / "model"
model_dir.mkdir(parents=True, exist_ok=True)

model_path = model_dir / "expense_categorization_pipeline.pkl"
joblib.dump(model, model_path)
print("Saved model to:", model_path)