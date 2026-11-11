from src.financial_assistant.hybrid_retriever import HybridFaqRetriever


def test_hybrid_retriever_finds_expense_categorization():
    retriever = HybridFaqRetriever()
    results = retriever.retrieve(
        "How do I categorize an expense?",
        top_k=3,
    )
    assert results
    assert results[0]["id"] == "faq-002"


def test_hybrid_retriever_finds_expense_export():
    retriever = HybridFaqRetriever()
    results = retriever.retrieve(
        "How can I export my expenses?",
        top_k=3,
    )
    assert results
    assert results[0]["id"] == "faq-005"


def test_hybrid_retriever_returns_scores():
    retriever = HybridFaqRetriever()
    results = retriever.retrieve("What does cash flow mean?", top_k=3)

    assert results
    assert all("bm25_score" in item for item in results)
    assert all("tfidf_score" in item for item in results)
    assert all("hybrid_score" in item for item in results)


def test_hybrid_retriever_handles_empty_query():
    retriever = HybridFaqRetriever()
    assert retriever.retrieve("") == []


def test_hybrid_retriever_handles_unsupported_query():
    retriever = HybridFaqRetriever()
    assert retriever.retrieve(
        "Does HisabDo integrate with QuickBooks?"
    ) == []


def test_hybrid_retriever_respects_top_k():
    retriever = HybridFaqRetriever()
    results = retriever.retrieve(
        "expense tracking and cash flow",
        top_k=2,
    )
    assert len(results) <= 2
