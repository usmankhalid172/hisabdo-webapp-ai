"""
ML classifier — the second half of Day 15 §6.2's "rule-based fallback +
ML/LLM model". Trained on data/sample_expenses.csv.

Day 15 §10 blocker: no approved production-grade labeled dataset exists yet.
This uses ad hoc/synthetic sample data, which is a known limitation carried
into Day 16 evidence (see Day 16 doc §2) — good enough to prove the pipeline
end-to-end, not to ship to production.
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_expenses.csv"
MODEL_PATH = Path(__file__).resolve().parent / "model_artifact.joblib"


def _build_text(row: pd.Series) -> str:
    return f"{row['description']} {row.get('merchant', '')}"


def train() -> Pipeline:
    df = pd.read_csv(DATA_PATH)
    X = df.apply(_build_text, axis=1)
    y = df["category"]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(X, y)
    joblib.dump(pipeline, MODEL_PATH)
    return pipeline


def load_or_train() -> Pipeline:
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return train()


class MLCategorizer:
    """Thin wrapper so the service layer doesn't touch sklearn directly."""

    def __init__(self):
        self._pipeline = load_or_train()

    def predict(self, description: str, merchant: str | None) -> tuple[str, float, list[str]]:
        text = f"{description} {merchant or ''}"
        probs = self._pipeline.predict_proba([text])[0]
        classes = self._pipeline.classes_

        ranked = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
        top_category, top_confidence = ranked[0]
        alternatives = [c for c, _ in ranked[1:3]]
        return top_category, float(top_confidence), alternatives


_ml_categorizer: MLCategorizer | None = None


def get_ml_categorizer() -> MLCategorizer:
    global _ml_categorizer
    if _ml_categorizer is None:
        _ml_categorizer = MLCategorizer()
    return _ml_categorizer
