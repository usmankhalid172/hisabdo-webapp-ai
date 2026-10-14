import pytest

from src.financial_assistant.intent_router import (
    classify_intent,
    extract_slots,
    get_missing_fields,
    build_follow_up,
)
from src.financial_assistant.service import _handle_transaction_intent


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Add an expense of 500 PKR", "expense"),
        ("Record income of 2000 PKR", "income"),
        ("Correct my expense", "correction"),
        ("Show my expenses", "report"),
        ("Categorize this transaction", "categorization"),
        ("What is my balance?", "private_account_query"),
        ("How do I use HisabDo?", "general_faq"),
    ],
)
def test_intent_classification(message, expected):
    assert classify_intent(message) == expected


def test_extract_amount_description_and_category():
    slots = extract_slots("Add expense of 500 PKR for groceries")
    assert slots["amount"] == "500"
    assert slots["description"] == "groceries"
    assert slots["category"] == "groceries"


def test_missing_amount_requests_amount():
    slots = extract_slots("Add expense for groceries")
    assert "amount" in get_missing_fields("expense", slots)


def test_missing_description_requests_description():
    slots = extract_slots("Add expense of 500 PKR")
    assert "description" in get_missing_fields("expense", slots)


def test_follow_up_for_missing_details():
    assert build_follow_up("expense", ["description"]) == (
        "Please describe the transaction."
    )


def test_follow_up_collects_missing_description():
    history = [
        {"role": "user", "content": "Add an expense of 500 PKR"},
        {"role": "assistant", "content": "Please describe the transaction."},
    ]
    result = _handle_transaction_intent("groceries", history, "test-1")
    assert result.intent == "expense"
    assert "500 PKR for groceries" in result.reply
    assert "not saved yet" in result.reply


def test_follow_up_collects_missing_amount():
    history = [
        {"role": "user", "content": "Add expense for groceries"},
        {"role": "assistant", "content": "What was the amount?"},
    ]
    result = _handle_transaction_intent("500", history, "test-2")
    assert result.intent == "expense"
    assert "500 PKR for groceries" in result.reply


def test_unrelated_message_does_not_start_transaction():
    result = _handle_transaction_intent(
        "How do I use HisabDo?", [], "test-3"
    )
    assert result is None
