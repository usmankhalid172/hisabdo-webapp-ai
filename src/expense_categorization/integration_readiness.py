from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "model" / "expense_categorization_pipeline.pkl"


class ExpenseIntegrationReadiness:
    """Integration-ready wrapper around the existing expense classifier."""

    def __init__(self, model_path=MODEL_PATH, confidence_threshold=0.50):
        self.model_path = Path(model_path)
        self.confidence_threshold = float(confidence_threshold)

        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0 and 1.")

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Expense categorization model not found: {self.model_path}"
            )

        self.model = joblib.load(self.model_path)

    def predict(self, description: str) -> dict:
        """Predict category and expose confidence for integration decisions."""

        if not isinstance(description, str):
            raise ValueError("Description must be a string.")

        description = description.strip()

        if not description:
            raise ValueError("Description cannot be empty.")

        category = self.model.predict([description])[0]
        probabilities = self.model.predict_proba([description])[0]
        confidence = float(probabilities.max())

        return {
            "category": str(category),
            "confidence": confidence,
            "accepted": confidence >= self.confidence_threshold,
        }