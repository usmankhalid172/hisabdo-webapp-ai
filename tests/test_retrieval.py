from pathlib import Path

from src.financial_assistant.rag.knowledge_base import (
    load_knowledge_base
)
from src.financial_assistant.rag.retriever import (
    FinancialRetriever
)


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sample_financial_knowledge.json"
)


def test_retriever_returns_relevant_result():
    documents = load_knowledge_base(str(DATA_PATH))
    retriever = FinancialRetriever(documents)

    results = retriever.retrieve(
        "What does profit mean?",
        top_k=3
    )

    assert len(results) > 0
    assert results[0]["id"] == "finance_001"


def test_retriever_handles_empty_query():
    documents = load_knowledge_base(str(DATA_PATH))
    retriever = FinancialRetriever(documents)

    results = retriever.retrieve("")

    assert results == []


def test_financial_retriever_rejects_invalid_query_and_limits():
    documents = load_knowledge_base(str(DATA_PATH))
    retriever = FinancialRetriever(documents)

    for query in (None, 123, "", "   "):
        assert retriever.retrieve(query) == []

    for top_k in (0, -1, 1.5, True, False, None):
        assert retriever.retrieve("What does profit mean?", top_k=top_k) == []

    for min_score in (-0.1, 1.1, float("nan"), float("inf"), True, "0.5"):
        assert retriever.retrieve(
            "What does profit mean?",
            min_score=min_score,
        ) == []


def test_faq_retriever_rejects_invalid_top_k(tmp_path):
    from src.financial_assistant.rag.retriever import FaqRetriever

    path = tmp_path / "faq_docs.json"
    path.write_text(
        '[{"id":"faq-1","title":"Profit","text":"Profit is revenue minus expenses.","verified":true}]',
        encoding="utf-8",
    )

    retriever = FaqRetriever(docs_path=path)

    for top_k in (0, -1, 1.5, True, False, None):
        assert retriever.retrieve("What is profit?", top_k=top_k) == []
