from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "model" / "expense_categorization_pipeline.pkl"

DEFAULT_CONFIDENCE_THRESHOLD = 0.50


class ExpensePredictionFinalizer:
    """Finalize expense-category predictions using model confidence."""

    def __init__(self, model_path=MODEL_PATH, confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD):
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")

        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.model = joblib.load(self.model_path)

    def predict(self, description):
        """Return a finalized category prediction for an expense description."""

        if not isinstance(description, str):
            raise ValueError("description must be a string")

        description = description.strip()

        if not description:
            raise ValueError("description must not be empty")

        probabilities = self.model.predict_proba([description])[0]
        predicted_index = probabilities.argmax()

        category = self.model.classes_[predicted_index]
        confidence = float(probabilities[predicted_index])

        accepted = confidence >= self.confidence_threshold

        return {
            "description": description,
            "category": category if accepted else "Other",
            "model_category": category,
            "confidence": round(confidence, 4),
            "accepted": accepted,
            "confidence_threshold": self.confidence_threshold,
        }
