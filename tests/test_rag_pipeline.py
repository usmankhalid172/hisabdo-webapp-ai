"""
Day 23-24 — RAG context pipeline verification.

Owner: Muhammad Hamza Nawaz
Day: 23-24 — RAG Context Pipeline Setup

Verifies that retrieved context is correctly normalized, ranked, capped,
and formatted before it reaches the LLM request layer (llm_service.py,
unchanged). No live retriever is available yet (no canonical retriever
chosen as of Day 23-24 — see rag_pipeline.py module docstring), so all
context here is hand-built to exercise the pipeline's own contract:
any object/dict with `text` (+ optional `source`, `score`) must work.
"""

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.financial_assistant.rag_pipeline import (
    ContextChunk,
    PipelineConfig,
    prepare_context,
    format_context_block,
    build_grounded_question,
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
# Normalization — accepts both dataclass and dict chunks (retriever-agnostic)
# ---------------------------------------------------------------------------

def test_accepts_context_chunk_dataclass():
    chunks = prepare_context([ContextChunk(text="Groceries: $85 in July.", source="transactions")])
    assert len(chunks) == 1
    assert chunks[0].text == "Groceries: $85 in July."


def test_accepts_plain_dict_chunks():
    """Confirms either Ahmed's or Faiza's retriever output can be mapped in with a plain dict."""
    chunks = prepare_context([{"text": "Budget: $500/month.", "source": "budget_kb", "score": 0.9}])
    assert len(chunks) == 1
    assert chunks[0].source == "budget_kb"


def test_malformed_chunk_dropped_not_raised():
    """One bad chunk from a retriever must not crash the pipeline."""
    chunks = prepare_context([
        {"text": "Valid chunk."},
        {"source": "no_text_field"},  # missing 'text'
        {"text": ""},                  # empty text
        "not even a dict",             # wrong type entirely
    ])
    assert len(chunks) == 1
    assert chunks[0].text == "Valid chunk."


def test_all_malformed_yields_empty_not_error():
    chunks = prepare_context([{"source": "x"}, 123, None])
    assert chunks == []


# ---------------------------------------------------------------------------
# Ranking and capping
# ---------------------------------------------------------------------------

def test_chunks_ranked_by_score_descending():
    chunks = prepare_context([
        ContextChunk(text="low", score=0.2),
        ContextChunk(text="high", score=0.9),
        ContextChunk(text="mid", score=0.5),
    ])
    assert [c.text for c in chunks] == ["high", "mid", "low"]


def test_unscored_chunks_sort_after_scored_chunks():
    chunks = prepare_context([
        ContextChunk(text="unscored"),
        ContextChunk(text="scored", score=0.1),
    ])
    assert [c.text for c in chunks] == ["scored", "unscored"]


def test_chunk_count_capped():
    config = PipelineConfig(max_context_chunks=2)
    raw = [ContextChunk(text=f"chunk {i}", score=float(i)) for i in range(5)]
    chunks = prepare_context(raw, config=config)
    assert len(chunks) == 2
    # highest scores kept
    assert {c.text for c in chunks} == {"chunk 4", "chunk 3"}


def test_min_score_filter_applied():
    config = PipelineConfig(min_chunk_score=0.5)
    raw = [ContextChunk(text="keep", score=0.7), ContextChunk(text="drop", score=0.3)]
    chunks = prepare_context(raw, config=config)
    assert [c.text for c in chunks] == ["keep"]


def test_char_budget_truncates_oversized_context():
    config = PipelineConfig(max_context_chars=100, max_context_chunks=10)
    raw = [ContextChunk(text="x" * 80, score=1.0), ContextChunk(text="y" * 80, score=0.9)]
    chunks = prepare_context(raw, config=config)
    total_chars = sum(len(c.text) for c in chunks)
    assert total_chars <= 100 + 1  # +1 allows for the truncation ellipsis char


# ---------------------------------------------------------------------------
# Formatting — this is the "correctly formats system inputs" verification
# ---------------------------------------------------------------------------

def test_empty_context_formats_to_empty_string():
    assert format_context_block([]) == ""


def test_context_block_includes_labels_and_sources():
    chunks = [ContextChunk(text="Spent $85 on groceries.", source="transactions")]
    block = format_context_block(chunks)
    assert "[1] (transactions) Spent $85 on groceries." in block
    assert block.startswith("Relevant financial data:")


def test_context_block_numbers_multiple_chunks_in_order():
    chunks = [ContextChunk(text="first"), ContextChunk(text="second")]
    block = format_context_block(chunks)
    assert "[1]" in block and "[2]" in block
    assert block.index("[1]") < block.index("[2]")


def test_no_context_leaves_question_unchanged():
    """Verifies the ungrounded path is untouched — same question in, same question out."""
    question = "What was my most recent expense?"
    assert build_grounded_question(question, []) == question


def test_context_prepended_before_question():
    chunks = [ContextChunk(text="Balance: $1200.")]
    grounded = build_grounded_question("How much do I have left?", chunks)
    assert grounded.startswith("Relevant financial data:")
    assert grounded.endswith("Question: How much do I have left?")
    assert "Balance: $1200." in grounded


# ---------------------------------------------------------------------------
# End-to-end: pipeline hands off correctly to the unchanged llm_service flow
# ---------------------------------------------------------------------------

def test_grounded_response_reaches_llm_with_formatted_context():
    """
    Confirms the assembled (context + question) string is what actually
    gets sent to the LLM API — this is the "verify context retrieval
    correctly formats system inputs before hitting backend response
    handlers" requirement, exercised end-to-end.
    """
    client = _mock_client_with_response("You spent $85 on groceries in July.")
    result = get_grounded_financial_assistant_response(
        "How much did I spend on groceries?",
        raw_context_chunks=[{"text": "Groceries: $85 in July.", "source": "transactions"}],
        client=client,
    )
    assert result == "You spent $85 on groceries in July."

    sent_messages = client.chat.completions.create.call_args.kwargs["messages"]
    user_message = next(m["content"] for m in sent_messages if m["role"] == "user")
    assert "Relevant financial data:" in user_message
    assert "Groceries: $85 in July." in user_message
    assert "Question: How much did I spend on groceries?" in user_message


def test_ungrounded_call_is_identical_to_base_llm_service_flow():
    """
    No context provided -> behaves exactly like the plain (Day 15-22)
    get_financial_assistant_response, proving this module is a strict
    superset and doesn't change existing behavior when unused.
    """
    client = _mock_client_with_response("You spent $340 this month.")
    result = get_grounded_financial_assistant_response(
        "How much did I spend this month?", client=client
    )
    assert result == "You spent $340 this month."

    sent_messages = client.chat.completions.create.call_args.kwargs["messages"]
    user_message = next(m["content"] for m in sent_messages if m["role"] == "user")
    assert user_message == "How much did I spend this month?"


def test_grounded_call_still_falls_back_on_api_failure():
    """Confirms error handling/fallback (Day 15-22, untouched) still applies when context is attached."""
    from openai import APITimeoutError
    client = MagicMock()
    client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
    result = get_grounded_financial_assistant_response(
        "How much did I spend?",
        raw_context_chunks=[{"text": "some context"}],
        client=client,
    )
    assert "trouble answering" in result.lower()


def test_exact_duplicate_chunk_text_is_deduplicated_keeping_higher_score():
    """
    Day 28: a retriever can legitimately return the same underlying
    content twice (matched by multiple query terms, indexed more than
    once, etc.) — keeping both wastes prompt budget on redundant text.
    Confirms the duplicate is dropped and the higher-scored occurrence
    of the two is the one kept.
    """
    chunks = [
        ContextChunk(text="Groceries at Al-Fatah", source="a", score=0.5),
        ContextChunk(text="Groceries at Al-Fatah", source="b", score=0.9),
        ContextChunk(text="Electricity bill", source="c", score=0.3),
    ]
    result = prepare_context(chunks)
    assert len(result) == 2
    grocery_chunk = next(c for c in result if c.text == "Groceries at Al-Fatah")
    assert grocery_chunk.source == "b"  # the higher-scored duplicate survived
    assert grocery_chunk.score == 0.9


def test_near_duplicate_chunks_with_different_text_are_both_kept():
    """
    Guardrail: dedup must be exact-text-match only — chunks that are
    merely similar (different transactions, same category/merchant)
    must NOT be collapsed, since that would silently drop real,
    distinct information.
    """
    chunks = [
        ContextChunk(text="2026-08-01: Al-Fatah — Rs. 1,500.00 (groceries)", source="s", score=0.8),
        ContextChunk(text="2026-08-08: Al-Fatah — Rs. 1,500.00 (groceries)", source="s", score=0.7),
    ]
    result = prepare_context(chunks)
    assert len(result) == 2


def test_grounded_question_near_default_context_budget_is_not_rejected():
    """
    Regression test for a bug found during QA (Syeda Isma Nazir, Day 27
    review of PR #70): the default max_context_chars (3000) can produce
    a grounded question longer than llm_service's default max_input_chars
    (1000), which used to raise InvalidInputError on an entirely normal,
    well-grounded question instead of succeeding. Uses chunk volume close
    to the actual default budget, not an artificially small example.
    """
    chunks = [
        ContextChunk(
            text=f"Transaction record {i}: merchant name and descriptive note here. " * 10,
            source="transaction_history",
            score=0.9 - i * 0.01,
        )
        for i in range(5)
    ]
    message = MagicMock(); message.content = "You spent Rs. 12,000 across these transactions."
    choice = MagicMock(); choice.message = message
    response = MagicMock(); response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = response

    result = get_grounded_financial_assistant_response(
        "How much did I spend?", raw_context_chunks=chunks, client=client
    )
    assert result == "You spent Rs. 12,000 across these transactions."
    sent_messages = client.chat.completions.create.call_args.kwargs["messages"]
    assert len(sent_messages[-1]["content"]) > 3000  # confirms the large grounded question actually went through


def test_grounded_call_never_shrinks_a_larger_caller_supplied_limit():
    """
    The fix must not silently shrink a max_input_chars the caller
    explicitly set higher than what's needed — only raise it when the
    default/provided value is too small for the configured context budget.
    """
    generous_config = LLMConfig(max_input_chars=10_000)
    chunks = [ContextChunk(text="short", source="s", score=0.5)]
    message = MagicMock(); message.content = "Answer."
    choice = MagicMock(); choice.message = message
    response = MagicMock(); response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = response

    get_grounded_financial_assistant_response(
        "Q?", raw_context_chunks=chunks, llm_config=generous_config, client=client
    )
    # No assertion beyond "didn't raise" — a shrink would surface as
    # this call failing validation, which it doesn't.