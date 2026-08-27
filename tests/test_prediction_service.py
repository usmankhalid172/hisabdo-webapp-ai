import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.expense_categorization.prediction_service import (
    ExpenseCategorizationService,
)


def test_prediction_returns_category():
    service = ExpenseCategorizationService()

    result = service.predict("Bought groceries from supermarket")

    assert isinstance(result, str)
    assert result != ""


def test_empty_description_is_rejected():
    service = ExpenseCategorizationService()

    with pytest.raises(ValueError, match="Description cannot be empty"):
        service.predict("")


def test_non_string_description_is_rejected():
    service = ExpenseCategorizationService()

    with pytest.raises(ValueError, match="Description must be a string"):
        service.predict(123)


def test_whitespace_description_is_rejected():
    service = ExpenseCategorizationService()

    with pytest.raises(ValueError, match="Description cannot be empty"):
        service.predict("   ")