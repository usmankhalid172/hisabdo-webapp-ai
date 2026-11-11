from src.financial_assistant.hybrid_retriever import HybridFaqRetriever
from src.financial_assistant.reranker import rerank_results


CASES = [
    ("How do I categorize an expense?", "faq-002"),
    ("How can I export my expenses?", "faq-005"),
    ("What does cash flow mean?", "finance_004"),
    ("What is the difference between profit and cash flow?", "faq-006"),
    ("What is a balance sheet?", "finance_007"),
]


def test_reranker_places_expected_document_first():
    retriever = HybridFaqRetriever()

    for query, expected_id in CASES:
        candidates = retriever.retrieve(query, top_k=10)
        results = rerank_results(query, candidates)
        assert results
        assert results[0]["id"] == expected_id


def test_reranker_preserves_original_rank():
    retriever = HybridFaqRetriever()
    candidates = retriever.retrieve(CASES[0][0], top_k=5)
    results = rerank_results(CASES[0][0], candidates)

    assert all("original_rank" in item for item in results)
    assert all("rerank_score" in item for item in results)


def test_reranker_does_not_modify_original_results():
    retriever = HybridFaqRetriever()
    candidates = retriever.retrieve(CASES[0][0], top_k=5)
    original_keys = [set(item.keys()) for item in candidates]

    rerank_results(CASES[0][0], candidates)

    assert [set(item.keys()) for item in candidates] == original_keys


def test_empty_query_returns_original_results():
    sample = [{"id": "faq-001", "title": "HisabDo"}]
    assert rerank_results("", sample) == sample


def test_empty_results_returns_empty_list():
    assert rerank_results("cash flow", []) == []


def test_reranker_keeps_all_candidates():
    retriever = HybridFaqRetriever()
    candidates = retriever.retrieve(CASES[0][0], top_k=5)
    results = rerank_results(CASES[0][0], candidates)

    assert len(results) == len(candidates)
