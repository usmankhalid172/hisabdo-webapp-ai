from src.financial_assistant.hybrid_retriever import (
    HybridFaqRetriever,
    normalize_query,
)


def test_normalize_case_and_whitespace():
    assert normalize_query("  HOW   DO I CATEGORIZE?  ") == "how do i categorize"


def test_normalize_surrounding_punctuation():
    assert normalize_query("...expense export!!!") == "expense export"


def test_normalize_preserves_roman_urdu_words():
    assert normalize_query("Main apne expenses kaise export karun?") == (
        "main apne expenses kaise export karun"
    )


def test_normalize_unicode_compatibility():
    assert normalize_query("ＦＩＮＡＮＣＥ") == "finance"


def test_equivalent_queries_return_same_ranking():
    r = HybridFaqRetriever()
    first = r.retrieve("How do I categorize an expense?")
    second = r.retrieve("  HOW DO I CATEGORIZE AN EXPENSE?  ")
    assert [x["id"] for x in first] == [x["id"] for x in second]


def test_roman_urdu_equivalent_queries_return_same_ranking():
    r = HybridFaqRetriever()
    first = r.retrieve("Main apne expenses ka record kaise export karun?")
    second = r.retrieve("main apne expenses ka record kaise export karun")
    assert [x["id"] for x in first] == [x["id"] for x in second]
