"""
Day 26 — retrieval/formatting hardening tests.

Owner: Muhammad Hamza Nawaz
Day: 26 — RAG Context Pipeline Setup (ensure retrieved transaction
contexts are correctly formatted before passing through backend
response handlers)

Day 25 built and verified the vector store against clean sample data.
Day 26 verifies the same pipeline against messier, more realistic
transaction shapes: zero amounts, missing optional fields, special
characters, duplicate-looking entries, and larger volumes that exercise
the Day 23-24 pipeline's capping/truncation behavior together with
retrieval, not retrieval alone.
"""

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.financial_assistant.vector_store import Transaction, TransactionVectorStore
from src.financial_assistant.rag_pipeline import (
    prepare_context,
    format_context_block,
    get_grounded_financial_assistant_response,
    PipelineConfig,
)


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
# Messy transaction data
# ---------------------------------------------------------------------------

def test_zero_amount_transaction_formats_without_crashing():
    txn = Transaction("t0", "2026-08-01", 0.0, "refund", "Store", "")
    text = txn.to_display_text()
    assert "0.00" in text
    assert "Store" in text


def test_transaction_with_no_note_still_indexable():
    store = TransactionVectorStore()
    store.add(Transaction("t1", "2026-08-01", 500.0, "misc", "Unknown Vendor"))
    results = store.query("misc")
    assert len(results) == 1


def test_special_characters_in_note_do_not_break_formatting():
    store = TransactionVectorStore()
    store.add(Transaction(
        "t1", "2026-08-01", 1500.0, "dining", "Café Aylanto",
        "50% off — dinner w/ friends (Rs. discount applied)",
    ))
    results = store.query("dinner discount")
    assert len(results) == 1
    block = format_context_block(prepare_context(results))
    assert "Café Aylanto" in block


def test_duplicate_transactions_both_retrievable_and_distinct_in_output():
    """
    Near-duplicate transactions (same merchant/category, different day)
    should both be retrievable and stay distinguishable in the formatted
    output — not silently collapsed into one.
    """
    store = TransactionVectorStore()
    store.add(Transaction("t1", "2026-08-01", 1500.0, "groceries", "Al-Fatah"))
    store.add(Transaction("t2", "2026-08-08", 1500.0, "groceries", "Al-Fatah"))
    results = store.query("groceries Al-Fatah", top_k=5)
    assert len(results) == 2
    block = format_context_block(prepare_context(results))
    assert "2026-08-01" in block
    assert "2026-08-08" in block


def test_large_transaction_volume_still_respects_pipeline_cap():
    """
    With many matching transactions, the Day 23-24 pipeline's
    max_context_chunks cap (not the vector store's top_k) is what
    ultimately bounds what reaches the LLM — verifies the two layers
    compose correctly together rather than just in isolation.
    """
    store = TransactionVectorStore()
    for i in range(30):
        store.add(Transaction(f"t{i}", f"2026-08-{(i % 28) + 1:02d}", 100.0 + i, "groceries", "Al-Fatah"))

    results = store.query("groceries", top_k=30)  # ask the store for all matches
    assert len(results) == 30

    config = PipelineConfig(max_context_chunks=5)
    prepared = prepare_context(results, config=config)
    assert len(prepared) == 5


def test_messy_data_end_to_end_reaches_llm_without_error():
    """
    Combines several messy conditions in one store and confirms the full
    grounded pipeline still succeeds and formats cleanly.
    """
    store = TransactionVectorStore()
    store.add_many([
        Transaction("t1", "2026-08-01", 0.0, "refund", "Store A", ""),
        Transaction("t2", "2026-08-02", 1500.0, "dining", "Café Aylanto", "50% off — dinner"),
        Transaction("t3", "2026-08-03", 1500.0, "groceries", "Al-Fatah"),
        Transaction("t4", "2026-08-03", 1500.0, "groceries", "Al-Fatah"),
    ])
    context_chunks = store.query("groceries and dining this week", top_k=10)

    client = _mock_client_with_response("Here is a summary of your recent spending.")
    result = get_grounded_financial_assistant_response(
        "What did I spend on this week?",
        raw_context_chunks=context_chunks,
        client=client,
    )
    assert result == "Here is a summary of your recent spending."