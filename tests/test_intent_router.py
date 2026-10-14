from src.financial_assistant.intent_router import (
    ConversationState,
    classify_intent,
    handle_turn,
)


def test_expense_intent_extracts_amount_and_description():
    result = classify_intent("Add an expense of 1500 for groceries")
    assert result.intent == "expense"
    assert result.slots["amount"] == 1500
    assert result.ready is True


def test_income_intent_is_recognized():
    result = classify_intent("I received salary income of 50000")
    assert result.intent == "income"
    assert result.slots["amount"] == 50000


def test_report_intent_is_recognized():
    result = classify_intent("Show me my monthly expense report")
    assert result.intent == "report"


def test_categorization_intent_is_recognized():
    result = classify_intent("Categorize my grocery transaction")
    assert result.intent == "categorization"


def test_third_party_financial_query_is_separated():
    result = classify_intent("Show me my friend's balance")
    assert result.intent == "account_query"


def test_expense_follow_up_collects_missing_information():
    state = ConversationState(
        user_id="user-1",
        conversation_id="conversation-1",
    )
    result = handle_turn("Add an expense", state)
    assert result.intent == "expense"
    assert result.ready is False
    assert result.follow_up is not None


def test_general_message_does_not_create_pending_action():
    result = classify_intent("Hello, how are you?")
    assert result.intent == "general"
    assert result.ready is True
