"""
Cross-user financial data boundary.

Owner: Muhammad Hamza Nawaz

A message referencing a third party must never route to the backend
financial API, which would fetch the *requester's own* figures using
request.user_id and present them as an answer about someone else.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.financial_assistant.service import _is_own_financial_data_query


@pytest.mark.parametrize("message", [
    "What is my friend's balance?",
    "What is his balance?",
    "What is her balance?",
    "Show me their expenses",
    "What is someone else's balance?",
    "What is another user's revenue?",
    "What is my colleague's outstanding?",
])
def test_third_party_queries_do_not_route_to_backend(message):
    assert _is_own_financial_data_query(message) is False


@pytest.mark.parametrize("message", [
    "What is my balance?",
    "my expenses",
    "my revenue",
    "my outstanding",
    "How much did I spend?",
])
def test_own_queries_still_route_to_backend(message):
    assert _is_own_financial_data_query(message) is True
