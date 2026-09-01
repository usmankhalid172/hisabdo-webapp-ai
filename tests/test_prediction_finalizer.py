import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.expense_categorization.prediction_finalizer import (
    ExpensePredictionFinalizer,
)


def test_prediction_returns_expected_response_structure():
    service = ExpensePredictionFinalizer(confidence_threshold=0.0)

    result = service.predict("Electricity bill payment")

    assert set(result.keys()) == {
        "description",
        "category",
        "model_category",
        "confidence",
        "accepted",
        "confidence_threshold",
    }

    assert result["description"] == "Electricity bill payment"
    assert isinstance(result["category"], str)
    assert isinstance(result["confidence"], float)
    assert result["accepted"] is True


def test_high_confidence_prediction_is_accepted():
    service = ExpensePredictionFinalizer(confidence_threshold=0.0)

    result = service.predict("Electricity bill payment")

    assert result["accepted"] is True
    assert result["category"] == result["model_category"]


def test_very_high_threshold_returns_fallback():
    service = ExpensePredictionFinalizer(confidence_threshold=1.0)

    result = service.predict("Random unusual purchase")

    assert result["accepted"] is False
    assert result["category"] == "Other"
    assert result["model_category"] != ""


def test_empty_description_is_rejected():
    service = ExpensePredictionFinalizer()

    with pytest.raises(ValueError, match="must not be empty"):
        service.predict("   ")


def test_non_string_description_is_rejected():
    service = ExpensePredictionFinalizer()

    with pytest.raises(ValueError, match="must be a string"):
        service.predict(None)


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValueError, match="between 0 and 1"):
        ExpensePredictionFinalizer(confidence_threshold=1.5)
