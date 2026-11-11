from src.financial_assistant.hybrid_retriever import HybridFaqRetriever


def test_product_area_filter():
    r = HybridFaqRetriever()
    results = r.retrieve("expense category", product_area="HisabDo Expenses")
    assert [x["id"] for x in results] == ["faq-002"]


def test_category_filter():
    r = HybridFaqRetriever()
    results = r.retrieve("cash flow", category="Cash Flow")
    assert [x["id"] for x in results] == ["finance_004", "faq-004"]


def test_section_filter():
    r = HybridFaqRetriever()
    results = r.retrieve("expense category", section="Expense Tracking")
    assert [x["id"] for x in results] == ["faq-002"]


def test_combined_metadata_filters():
    r = HybridFaqRetriever()
    results = r.retrieve(
        "expense category",
        product_area="HisabDo Expenses",
        category="Expense Categorization",
        section="Expense Tracking",
    )
    assert [x["id"] for x in results] == ["faq-002"]


def test_metadata_filters_are_case_insensitive():
    r = HybridFaqRetriever()
    results = r.retrieve("expense category", product_area="hisabdo expenses")
    assert [x["id"] for x in results] == ["faq-002"]


def test_nonexistent_metadata_value_returns_empty():
    r = HybridFaqRetriever()
    results = r.retrieve("expense category", product_area="Unknown Product")
    assert results == []
