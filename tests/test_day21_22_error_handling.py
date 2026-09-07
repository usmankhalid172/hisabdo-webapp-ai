"""
Day 21-22 — sample failure/recovery evidence for prompt improvement and
LLM/API error-handling improvements.

Owner: Muhammad Hamza Nawaz
Day: 21-22 — LLM Error Handling & Prompt Improvement

Covers the two behaviors added this cycle (see llm_service.py):
    1. Rate-limit-specific handling (separate backoff, distinct exception).
    2. Inconsistent-response detection (echo responses, punctuation-only
       responses) as a new response-validation check.

Does not repeat Day 15/17 coverage (see tests/test_llm_service.py and
tests/test_use_cases_day17.py) — only the new behavior is tested here.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.financial_assistant.llm_service import (
    get_financial_assistant_response,
    validate_llm_response,
    LLMConfig,
    InvalidResponseError,
)
from openai import RateLimitError


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


def _mock_rate_limit_error() -> RateLimitError:
    response = MagicMock()
    response.status_code = 429
    return RateLimitError("Rate limit exceeded", response=response, body=None)


# ---------------------------------------------------------------------------
# Rate-limit handling
# ---------------------------------------------------------------------------

def test_rate_limit_triggers_longer_backoff_then_recovers_on_retry():
    """
    Sample recovery scenario: first call is rate-limited, retry succeeds.
    Confirms the rate-limit path is distinct from the generic retry path
    (uses config.rate_limit_backoff_seconds) and that recovery works.
    """
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _mock_rate_limit_error(),
        _mock_client_with_response("You spent $50 on transport.").chat.completions.create.return_value,
    ]
    config = LLMConfig(max_retries=1, rate_limit_backoff_seconds=0.01)  # fast for the test
    result = get_financial_assistant_response(
        "How much did I spend on transport?", config=config, client=client
    )
    assert result == "You spent $50 on transport."
    assert client.chat.completions.create.call_count == 2


def test_rate_limit_exhausted_falls_back_gracefully():
    """
    Sample failure scenario: rate limit persists through the retry budget,
    the user still gets the safe fallback message, not an exception or a
    raw 429.
    """
    client = MagicMock()
    client.chat.completions.create.side_effect = _mock_rate_limit_error()
    config = LLMConfig(max_retries=1, rate_limit_backoff_seconds=0.01)
    result = get_financial_assistant_response(
        "How much did I spend on transport?", config=config, client=client
    )
    assert "trouble answering" in result.lower()


# ---------------------------------------------------------------------------
# Inconsistent-response detection
# ---------------------------------------------------------------------------

def test_echo_response_rejected_and_recovers_on_retry():
    """
    Sample recovery scenario: the model's first reply is a bare echo of
    the question (a known inconsistent-response failure mode), rejected
    by validation, then a real answer comes back on retry.
    """
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _mock_client_with_response("How much did I spend this month?").chat.completions.create.return_value,
        _mock_client_with_response("You spent $340 this month.").chat.completions.create.return_value,
    ]
    config = LLMConfig(max_retries=1)
    result = get_financial_assistant_response(
        "How much did I spend this month?", config=config, client=client
    )
    assert result == "You spent $340 this month."


def test_echo_response_exhausted_falls_back():
    """Sample failure scenario: every attempt echoes the question — fallback returned, not the echo."""
    client = _mock_client_with_response("How much did I spend this month?")
    config = LLMConfig(max_retries=1)
    result = get_financial_assistant_response(
        "How much did I spend this month?", config=config, client=client
    )
    assert "trouble answering" in result.lower()


def test_punctuation_only_response_rejected_directly():
    """A response that's just symbols/punctuation is caught by validate_llm_response directly."""
    with pytest.raises(InvalidResponseError):
        validate_llm_response("...")


def test_legitimate_short_answer_not_rejected():
    """
    Guardrail: the new checks must not reject genuinely short, valid
    answers — only degenerate ones. "$85." is short but has real content.
    """
    result = validate_llm_response("$85.", user_question="How much on groceries?")
    assert result == "$85."


def test_exact_echo_with_different_punctuation_still_caught():
    """Echo detection should ignore trailing punctuation differences."""
    with pytest.raises(InvalidResponseError):
        validate_llm_response(
            "how much did i spend this month",
            user_question="How much did I spend this month?",
        )