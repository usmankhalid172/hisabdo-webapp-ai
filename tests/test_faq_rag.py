
import json

from src.financial_assistant.faq_rag import FaqRetriever


def write_kb(tmp_path, documents):
    """Create a temporary knowledge-base JSON file."""
    path = tmp_path / "faq_docs.json"
    path.write_text(
        json.dumps(documents),
        encoding="utf-8",
    )
    return path


def test_unverified_documents_are_not_retrieved(tmp_path):
    path = write_kb(
        tmp_path,
        [
            {
                "id": "faq-001",
                "title": "What is HisabDo?",
                "text": "A bookkeeping application.",
                "type": "product_faq",
                "version": "1.0.0",
                "verified": False,
                "source": "Test fixture",
            }
        ],
    )

    retriever = FaqRetriever(docs_path=path)

    assert retriever.documents == []
    assert retriever.retrieve("What is HisabDo?") == []


def test_verified_document_includes_source_and_version(tmp_path):
    path = write_kb(
        tmp_path,
        [
            {
                "id": "finance-001",
                "title": "What is profit?",
                "text": "Profit is revenue minus expenses.",
                "type": "finance_faq",
                "version": "1.2.0",
                "verified": True,
                "source": "Approved finance FAQ",
            }
        ],
    )

    retriever = FaqRetriever(
        docs_path=path,
        relevance_threshold=0.0,
    )

    matches = retriever.retrieve("What is profit?", top_k=1)

    assert len(matches) == 1

    result = matches[0]
    assert result["id"] == "finance-001"
    assert result["source"] == "Approved finance FAQ"
    assert result["version"] == "1.2.0"
    assert result["type"] == "finance_faq"
    assert result["verified"] is True


def test_empty_query_returns_no_results(tmp_path):
    path = write_kb(tmp_path, [])

    retriever = FaqRetriever(docs_path=path)

    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []


def test_invalid_relevance_threshold_is_rejected(tmp_path):
    path = write_kb(tmp_path, [])

    try:
        FaqRetriever(
            docs_path=path,
            relevance_threshold=1.5,
        )
    except ValueError as exc:
        assert "relevance_threshold" in str(exc)
    else:
        raise AssertionError(
            "An invalid relevance threshold should raise ValueError."
        )


def test_missing_knowledge_base_raises_error(tmp_path):
    missing_path = tmp_path / "missing.json"

    try:
        FaqRetriever(docs_path=missing_path)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError(
            "A missing knowledge base should raise FileNotFoundError."
        )


def test_day1_workflow_queries_do_not_return_unrelated_context():
    from src.financial_assistant.faq_rag import _day1_allowed_document_ids

    queries = [
        "How do I categorize an expense?",
        "What if the predicted category is wrong?",
        "How can I view my total income and expenses in HisabDo?",
        "How do I add a new customer in HisabDo?",
        "How do I record a new expense in HisabDo?",
    ]

    for query in queries:
        assert _day1_allowed_document_ids(query) == set(), query


def test_day1_overview_and_pdf_queries_have_document_allowlists():
    from src.financial_assistant.faq_rag import _day1_allowed_document_ids

    assert _day1_allowed_document_ids(
        "What can I do with HisabDo?"
    ) == {"faq-001"}

    assert _day1_allowed_document_ids(
        "How do I generate a PDF report in HisabDo?"
    ) == {"faq-005"}
