import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.expense_categorization.integration_readiness import (
    ExpenseIntegrationReadiness,
)


MODEL_PATH = ROOT / "model" / "expense_categorization_pipeline.pkl"


@pytest.fixture
def service():
    return ExpenseIntegrationReadiness(model_path=MODEL_PATH)


def test_valid_expense_returns_category_confidence_and_decision(service):
    result = service.predict("Uber ride to university")

    assert isinstance(result, dict)
    assert "category" in result
    assert "confidence" in result
    assert "accepted" in result

    assert isinstance(result["category"], str)
    assert isinstance(result["confidence"], float)
    assert isinstance(result["accepted"], bool)

    assert 0.0 <= result["confidence"] <= 1.0


def test_known_expense_categories_are_returned(service):
    test_cases = {
        "KFC dinner": "Food",
        "Uber ride to university": "Transport",
        "Electricity bill payment": "Utilities",
        "Pharmacy medicine": "Healthcare",
    }

    for description, expected_category in test_cases.items():
        result = service.predict(description)

        assert result["category"] == expected_category


def test_confidence_threshold_controls_acceptance():
    service = ExpenseIntegrationReadiness(
        model_path=MODEL_PATH,
        confidence_threshold=0.40,
    )

    result = service.predict("Uber ride to university")

    assert result["confidence"] >= 0.40
    assert result["accepted"] is True


def test_high_threshold_can_reject_prediction():
    service = ExpenseIntegrationReadiness(
        model_path=MODEL_PATH,
        confidence_threshold=0.90,
    )

    result = service.predict("Uber ride to university")

    assert result["confidence"] < 0.90
    assert result["accepted"] is False


@pytest.mark.parametrize(
    "description",
    [
        "",
        "   ",
    ],
)
def test_empty_descriptions_are_rejected(service, description):
    with pytest.raises(ValueError, match="Description cannot be empty"):
        service.predict(description)


@pytest.mark.parametrize(
    "description",
    [
        None,
        12345,
        ["Uber ride"],
        {"description": "Uber ride"},
    ],
)
def test_non_string_descriptions_are_rejected(service, description):
    with pytest.raises(ValueError, match="Description must be a string"):
        service.predict(description)


@pytest.mark.parametrize(
    "threshold",
    [
        -0.1,
        1.1,
    ],
)
def test_invalid_confidence_threshold_is_rejected(threshold):
    with pytest.raises(
        ValueError,
        match="Confidence threshold must be between 0 and 1",
    ):
        ExpenseIntegrationReadiness(
            model_path=MODEL_PATH,
            confidence_threshold=threshold,
        )


def test_missing_model_is_rejected(tmp_path):
    missing_model = tmp_path / "missing_model.pkl"

    with pytest.raises(FileNotFoundError, match="model not found"):
        ExpenseIntegrationReadiness(model_path=missing_model)