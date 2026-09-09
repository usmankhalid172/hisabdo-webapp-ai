"""
Day 25 — vector database retrieval tests.

Owner: Muhammad Hamza Nawaz
Day: 25 — RAG Context Pipeline Setup (wire up vector database retrieval)

Verifies vector_store.py in isolation, and end-to-end through the
Day 23-24 rag_pipeline.py into a mocked llm_service call — confirming
retrieved transaction context reaches the backend response handler
correctly formatted, as this task requires.
"""

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.financial_assistant.vector_store import (
    Transaction,
    TransactionVectorStore,
    build_sample_transaction_store,
)
from src.financial_assistant.rag_pipeline import (
    prepare_context,
    format_context_block,
    get_grounded_financial_assistant_response,
)
from src.financial_assistant.llm_service import LLMConfig


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
# TransactionVectorStore behavior
# ---------------------------------------------------------------------------

def test_empty_store_returns_no_results():
    store = TransactionVectorStore()
    assert store.query("groceries") == []


def test_query_ranks_more_relevant_transactions_higher():
    store = build_sample_transaction_store()
    results = store.query("grocery shopping")
    assert len(results) > 0
    # The two "groceries" category transactions should outrank unrelated ones.
    categories_in_top_results = [r.text for r in results[:3]]
    assert any("groceries" in text.lower() for text in categories_in_top_results)


def test_query_returns_context_chunks_with_source_and_score():
    store = build_sample_transaction_store()
    results = store.query("electricity bill")
    assert len(results) > 0
    top = results[0]
    assert top.source == "transaction_history"
    assert top.score is not None and top.score > 0
    assert "K-Electric" in top.text or "utilities" in top.text.lower()


def test_top_k_limits_result_count():
    store = build_sample_transaction_store()
    results = store.query("transaction", top_k=2)
    assert len(results) <= 2


def test_irrelevant_query_returns_no_or_low_scoring_results():
    store = build_sample_transaction_store()
    results = store.query("xyzxyz nonexistent gibberish term")
    assert results == []


def test_transaction_display_text_is_consistently_formatted():
    txn = Transaction("t1", "2026-08-15", 1234.5, "dining", "KFC", "lunch")
    text = txn.to_display_text()
    assert "2026-08-15" in text
    assert "KFC" in text
    assert "1,234.50" in text
    assert "dining" in text


# ---------------------------------------------------------------------------
# End-to-end: vector store -> pipeline -> LLM (mocked)
# ---------------------------------------------------------------------------

def test_vector_retrieval_reaches_llm_correctly_formatted():
    """
    The core Day 25 verification: retrieved transaction context is
    correctly formatted before it reaches the backend response handler
    (here, the mocked LLM call stands in for the response handler).
    """
    store = build_sample_transaction_store()
    context_chunks = store.query("groceries this month", top_k=3)

    client = _mock_client_with_response("You spent Rs. 6,650 on groceries this month.")
    result = get_grounded_financial_assistant_response(
        "How much did I spend on groceries?",
        raw_context_chunks=context_chunks,
        client=client,
    )
    assert result == "You spent Rs. 6,650 on groceries this month."

    sent_messages = client.chat.completions.create.call_args.kwargs["messages"]
    user_message = sent_messages[-1]["content"]
    assert "Relevant financial data" in user_message
    assert "groceries" in user_message.lower()
    assert "transaction_history" in user_message


def test_no_matching_transactions_falls_through_ungrounded():
    """
    A query with no relevant transactions in the store should not break
    the pipeline — it should just proceed ungrounded (same as Day 23-24
    behavior with no context), not error out.
    """
    store = TransactionVectorStore()  # empty store
    context_chunks = store.query("anything")
    assert context_chunks == []

    client = _mock_client_with_response("I don't have enough information to answer that.")
    result = get_grounded_financial_assistant_response(
        "How much did I spend on groceries?",
        raw_context_chunks=context_chunks,
        client=client,
    )
    assert result == "I don't have enough information to answer that."