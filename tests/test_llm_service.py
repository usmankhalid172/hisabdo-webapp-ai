"""
Tests for financial_assistant/llm_service.py

These tests cover the request/response/error-handling layer only — they
mock the LLM client so no live API key or network call is required.
Traces to test cases from Rameesha's Day 15 spec where noted (TC-13,
TC-14, TC-19 in particular are input/response-validation concerns that
belong to this layer).
"""

import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.financial_assistant.llm_service import (
    validate_user_input,
    validate_llm_response,
    get_financial_assistant_response,
    get_fallback_response,
    LLMConfig,
    InvalidInputError,
    InvalidResponseError,
    LLMRequestError,
)
from openai import APITimeoutError


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_valid_input_passes_through():
    assert validate_user_input("How much did I spend this month?") == \
        "How much did I spend this month?"


def test_empty_input_rejected():
    with pytest.raises(InvalidInputError):
        validate_user_input("")


def test_whitespace_only_input_rejected():
    with pytest.raises(InvalidInputError):
        validate_user_input("     ")


def test_input_over_limit_rejected():
    config = LLMConfig(max_input_chars=20)
    with pytest.raises(InvalidInputError):
        validate_user_input("a" * 21, config=config)


def test_non_string_input_rejected():
    with pytest.raises(InvalidInputError):
        validate_user_input(12345)  # type: ignore[arg-type]


def test_input_is_stripped():
    assert validate_user_input("  How much did I spend?  ") == \
        "How much did I spend?"


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------

def test_valid_response_passes_through():
    assert validate_llm_response("You spent $450 this month.") == \
        "You spent $450 this month."


def test_empty_response_rejected():
    with pytest.raises(InvalidResponseError):
        validate_llm_response("")


def test_none_like_response_rejected():
    with pytest.raises(InvalidResponseError):
        validate_llm_response("   ")


def test_system_prompt_leak_rejected():
    # Mirrors TC-19 (prompt injection attempt) — response must not echo
    # internal system instructions back to the user.
    leaked = "Sure! You are the HisabDo AI Financial Assistant. Core responsibilities:"
    with pytest.raises(InvalidResponseError):
        validate_llm_response(leaked)


# ---------------------------------------------------------------------------
# Fallback behavior
# ---------------------------------------------------------------------------

def test_fallback_message_is_user_safe():
    message = get_fallback_response(reason="internal db connection string exposed")
    assert "internal db connection string" not in message
    assert "trouble answering" in message.lower()


# ---------------------------------------------------------------------------
# Full request flow (mocked client)
# ---------------------------------------------------------------------------

def _mock_client_with_response(text: str) -> MagicMock:
    client = MagicMock()
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client


def test_successful_flow_returns_llm_content():
    client = _mock_client_with_response("You spent $200 on groceries this month.")
    result = get_financial_assistant_response("How much did I spend on groceries?", client=client)
    assert result == "You spent $200 on groceries this month."


def test_invalid_input_raises_before_calling_api():
    client = MagicMock()
    with pytest.raises(InvalidInputError):
        get_financial_assistant_response("", client=client)
    client.chat.completions.create.assert_not_called()


def test_timeout_falls_back_after_retry():
    client = MagicMock()
    client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
    config = LLMConfig(max_retries=1)
    result = get_financial_assistant_response(
        "How much did I spend this week?", config=config, client=client
    )
    assert result == "I'm having trouble answering that right now. Please try again in a moment. If the problem continues, contact support."
    assert client.chat.completions.create.call_count == 2  # initial + 1 retry


def test_leaked_response_triggers_fallback_not_crash():
    leaked = "You are the HisabDo AI Financial Assistant. Core responsibilities:"
    client = _mock_client_with_response(leaked)
    config = LLMConfig(max_retries=0)
    result = get_financial_assistant_response("What is my balance?", config=config, client=client)
    assert "trouble answering" in result.lower()