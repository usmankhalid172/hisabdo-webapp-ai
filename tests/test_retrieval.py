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