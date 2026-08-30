from pathlib import Path
import joblib


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "model" / "expense_categorization_pipeline.pkl"


class ExpenseCategorizationService:
    """Service for predicting expense categories."""

    def __init__(self, model_path=MODEL_PATH):
        self.model_path = Path(model_path)
        self.model = None

    def load_model(self):
        """Load the trained ML pipeline."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        self.model = joblib.load(self.model_path)

    def predict(self, description: str) -> str:
        """Predict an expense category from its description."""

        if not isinstance(description, str):
            raise ValueError("Description must be a string.")

        description = description.strip()

        if not description:
            raise ValueError("Description cannot be empty.")

        if self.model is None:
            self.load_model()

        prediction = self.model.predict([description])

        if prediction is None or len(prediction) == 0:
            raise ValueError("Model did not return a prediction.")

        return str(prediction[0])