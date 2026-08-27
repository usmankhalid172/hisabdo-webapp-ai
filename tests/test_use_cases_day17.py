"""
Day 17 — realistic use-case validation for financial_assistant/llm_service.py

Owner: Muhammad Hamza Nawaz
Day: 17 — Validate practical AI Assistant use cases using Day 15/16 work

Purpose
-------
Day 15/16 tests proved the request/response/error-handling *mechanics* of
llm_service.py in isolation (generic strings, mocked client). Day 17 asks a
different question: for realistic user questions drawn from Rameesha's Day 15
question categories (PR #4, sections 5.1-5.8), what actually works today?

This module does NOT re-test validation/error-handling logic already covered
by tests/test_llm_service.py (see that file for TC-level coverage). It tests
llm_service.py's behavior specifically against realistic per-category inputs,
and documents where a category is fully exercisable at this layer vs. where
it is blocked on the data-retrieval/RAG layer that this module intentionally
does not own (see llm_service.py module docstring, "This module does NOT
define: The financial data retrieval / RAG layer").

No live LLM API key is available in this environment (Asim's model/API
research has not landed a branch/PR as of Day 17 — see area notes). All
tests below mock the OpenAI client, per Team Lead's Day 16 guidance that
mocked tests remain the evidence until a provider is finalized.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.financial_assistant.llm_service import (
    get_financial_assistant_response,
    validate_user_input,
    LLMConfig,
    InvalidInputError,
)
from openai import APITimeoutError


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


# ---------------------------------------------------------------------------
# 5.1 Expense Summary Questions
# ---------------------------------------------------------------------------

def test_expense_summary_question_flows_through_validation_and_returns_llm_text():
    """
    'How much did I spend this month?' — request/response layer passes the
    question through and returns whatever the model answers. This layer
    does NOT verify the number is correct, because it has no access to the
    user's transaction data (that's the retrieval layer's job). Flagged as
    PARTIALLY WORKING for the use-case as a whole: mechanics work, grounding
    does not yet exist.
    """
    client = _mock_client_with_response("You spent $340 this month.")
    result = get_financial_assistant_response(
        "How much did I spend this month?", client=client
    )
    assert result == "You spent $340 this month."
    # This layer cannot assert the $340 figure is real — no data was passed in.


# ---------------------------------------------------------------------------
# 5.2 Category-Based Questions
# ---------------------------------------------------------------------------

def test_category_question_flows_through_but_is_not_grounded():
    """
    'How much did I spend on groceries?' — same limitation as above, called
    out explicitly since category-based answers are the most hallucination-
    prone without grounding (Rameesha's rule: "No hallucination").
    """
    client = _mock_client_with_response("You spent $85 on groceries.")
    result = get_financial_assistant_response(
        "How much did I spend on groceries?", client=client
    )
    assert result == "You spent $85 on groceries."


# ---------------------------------------------------------------------------
# 5.3 Transaction Questions
# ---------------------------------------------------------------------------

def test_transaction_lookup_question_blocked_without_retrieval():
    """
    'What was my most recent expense?' cannot be meaningfully answered by
    this layer at all — there is no transaction data available to inject,
    and a mocked "answer" here would just be a made-up transaction, which
    is the exact hallucination scenario Rameesha's spec prohibits. Recorded
    as BLOCKED pending the retrieval/RAG layer, not tested as "working".
    """
    pytest.skip(
        "BLOCKED: transaction-level answers require the data retrieval "
        "layer (owned by RAG/integration, see Ahmed Ali Ghori PR #18). "
        "This module has no mechanism to ground a transaction answer, so "
        "asserting a mocked response here would misrepresent this use "
        "case as working."
    )


# ---------------------------------------------------------------------------
# 5.4 Budget Questions
# ---------------------------------------------------------------------------

def test_budget_question_blocked_without_retrieval():
    """
    'How much budget do I have left?' — same blocker as transactions:
    no budget data source is wired into this module. BLOCKED.
    """
    pytest.skip(
        "BLOCKED: budget answers require budget/expense data this module "
        "does not have access to. Mechanics-only coverage would be "
        "misleading for this use case."
    )


# ---------------------------------------------------------------------------
# 5.5 Comparison Questions
# ---------------------------------------------------------------------------

def test_comparison_question_blocked_without_retrieval():
    """
    'Did I spend more this month than last month?' — requires two periods
    of grounded data. BLOCKED for the same reason as 5.3/5.4.
    """
    pytest.skip(
        "BLOCKED: multi-period comparison requires grounded historical "
        "data not available to this layer."
    )


# ---------------------------------------------------------------------------
# 5.6 Trend and Insight Questions
# ---------------------------------------------------------------------------

def test_trend_question_blocked_without_retrieval():
    """
    'What category do I spend the most on?' — BLOCKED, same reasoning.
    """
    pytest.skip(
        "BLOCKED: trend/insight answers require grounded aggregate data "
        "not available to this layer."
    )


# ---------------------------------------------------------------------------
# 5.7 Ambiguous Questions
# ---------------------------------------------------------------------------

def test_ambiguous_question_is_a_valid_request_this_layer_can_carry():
    """
    'How much did I spend?' (no period given) is NOT rejected by input
    validation — it is a well-formed string. Whether the model actually
    asks a clarifying question instead of guessing is a prompt-engineering
    / model-behavior concern (Rameesha's spec, section 3.3), not something
    this request/response layer enforces. WORKING at this layer: the
    question passes validation and reaches the model; PARTIALLY WORKING
    for the full use case since the clarification behavior itself is
    untested without a live model.
    """
    client = _mock_client_with_response(
        "Which period would you like me to check — today, this week, "
        "this month, or another period?"
    )
    result = get_financial_assistant_response("How much did I spend?", client=client)
    assert "period" in result.lower()


# ---------------------------------------------------------------------------
# 5.8 Unsupported / Out-of-Scope Questions
# ---------------------------------------------------------------------------

def test_unsupported_question_is_a_valid_request_this_layer_can_carry():
    """
    'Write me a Python program.' is off-topic for the assistant but is
    still a well-formed input — this layer's job is only to validate the
    *shape* of the input, not its subject matter (scope enforcement is a
    system-prompt / model-behavior concern). WORKING at this layer.
    """
    client = _mock_client_with_response(
        "I can only help with questions about your finances."
    )
    result = get_financial_assistant_response(
        "Write me a Python program.", client=client
    )
    assert result == "I can only help with questions about your finances."


# ---------------------------------------------------------------------------
# Cross-category error handling, using a realistic question as the carrier
# ---------------------------------------------------------------------------

def test_realistic_question_falls_back_when_model_unavailable():
    """
    Confirms the Day 15/16 fallback path holds for a realistic question,
    not just a placeholder string — the model is unreachable (timeout) and
    the user still gets the safe fallback message rather than an error.
    """
    client = MagicMock()
    client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
    config = LLMConfig(max_retries=1)
    result = get_financial_assistant_response(
        "How much did I spend on transportation this month?",
        config=config,
        client=client,
    )
    assert "trouble answering" in result.lower()


def test_empty_realistic_input_rejected_before_any_api_call():
    """
    A realistic empty-submit scenario (e.g. user hits send with a blank
    box) is rejected before any API call is attempted — no wasted request,
    no fallback needed.
    """
    client = MagicMock()
    with pytest.raises(InvalidInputError):
        get_financial_assistant_response("   ", client=client)
    client.chat.completions.create.assert_not_called()


def test_overlong_realistic_input_rejected():
    """
    A realistic "pasted a huge block of text" scenario is rejected by the
    existing length check rather than being sent to the model.
    """
    long_question = "How much did I spend on " + ("groceries " * 200)
    with pytest.raises(InvalidInputError):
        validate_user_input(long_question, config=LLMConfig(max_input_chars=200))