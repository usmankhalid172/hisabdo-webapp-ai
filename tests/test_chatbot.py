
import json

import pytest

from src.errors import ServiceError
from src.financial_assistant.service import handle_chat
from src.schemas import ChatbotRequest


def _verified_faq(
    faq_id="faq-002",
    title="How do I categorize an expense?",
    text=(
        "HisabDo helps organize business spending "
        "by assigning expenses to appropriate categories."
    ),
):
    """Return a test-only verified FAQ document."""
    return {
        "id": faq_id,
        "title": title,
        "text": text,
        "source": "Test verified FAQ",
        "type": "faq",
        "version": "test-1",
        "verified": True,
        "score": 0.9,
    }


def test_own_financial_data_query_fails_when_backend_unavailable():
    req = ChatbotRequest(
        user_id="user-1",
        message="What is my balance right now?",
        conversation_id="c1",
    )

    with pytest.raises(ServiceError) as exc_info:
        handle_chat(req)

    assert exc_info.value.status_code == 503
    assert "not available yet" in str(exc_info.value)


def test_product_faq_query_uses_rag(monkeypatch):
    class FakeRetriever:
        def retrieve(self, query, top_k=3):
            if (
                "categor" in query.lower()
                or "expense" in query.lower()
            ):
                return [
                    _verified_faq(
                        text=(
                            "Expense categorization organizes "
                            "business expenses into categories."
                        )
                    )
                ]
            return []

    monkeypatch.setattr(
        "src.financial_assistant.service.get_retriever",
        lambda: FakeRetriever(),
    )

    req = ChatbotRequest(
        user_id="user-1",
        message="How does automatic expense categorization work?",
        conversation_id="c2",
    )

    resp = handle_chat(req)

    assert resp.source == "rag"
    assert resp.intent == "product_faq"


def test_unrelated_query_falls_back_to_general():
    req = ChatbotRequest(
        user_id="user-1",
        message="asdkjhasd unrelated gibberish zzz",
        conversation_id="c3",
    )

    resp = handle_chat(req)

    assert resp.source == "llm_general"
    assert resp.intent == "general"


def test_chatbot_endpoint_returns_valid_shape(
    client,
    auth_headers,
    monkeypatch,
):
    class FakeRetriever:
        def retrieve(self, query, top_k=3):
            return [
                _verified_faq(
                    faq_id="finance-001",
                    title="Profit and cash flow",
                    text=(
                        "Profit is revenue minus expenses. "
                        "Cash flow tracks money entering "
                        "and leaving a business."
                    ),
                )
            ]

    monkeypatch.setattr(
        "src.financial_assistant.service.get_retriever",
        lambda: FakeRetriever(),
    )

    resp = client.post(
        "/api/v1/chatbot",
        json={
            "user_id": "user-1",
            "message": "What's the difference between profit and cash flow?",
            "conversation_id": "c4",
            "history": [],
        },
        headers=auth_headers,
    )

    assert resp.status_code == 200

    body = resp.json()

    for field in ("reply", "conversation_id", "source"):
        assert field in body

    assert body["source"] == "rag"


def test_history_is_passed_to_llm_provider(monkeypatch):
    """Verify that request history is forwarded to the LLM provider."""
    captured = {}

    class SpyProvider:
        def generate_reply(
            self,
            message,
            context=None,
            history=None,
        ):
            captured["history"] = history
            captured["message"] = message
            return "reply", 10

    monkeypatch.setattr(
        "src.financial_assistant.service.get_llm_provider",
        lambda: SpyProvider(),
    )

    history = [
        {
            "role": "user",
            "content": "How do I categorize an expense?",
        },
        {
            "role": "assistant",
            "content": "Rule-based + ML model.",
        },
    ]

    request = ChatbotRequest(
        user_id="test-user",
        message="What about the batch version?",
        conversation_id="test-convo",
        history=history,
    )

    handle_chat(request)

    assert captured["history"] == history


def test_mock_provider_does_not_mislabel_financial_data_as_docs():
    """Ensure financial context is not incorrectly described as docs."""
    from src.financial_assistant.llm_providers import MockLLMProvider

    provider = MockLLMProvider()

    reply, _ = provider.generate_reply(
        "What is my balance?",
        context="Balance: 100 PKR.",
    )

    assert "docs" not in reply.lower()


def test_weak_rag_match_falls_back_to_general_instead_of_wrong_answer():
    """Ensure weak FAQ matches do not produce irrelevant answers."""
    from src.financial_assistant.faq_rag import get_retriever

    matches = get_retriever().retrieve(
        "How can I get my spending data out of the app?",
        top_k=1,
    )

    assert matches == []


def test_strong_rag_match_still_retrieves(
    monkeypatch,
    tmp_path,
):
    """Verify semantic retrieval using a test-only verified FAQ."""
    from src.financial_assistant import faq_rag

    test_docs = [
        {
            "id": "faq-002",
            "title": "How do I categorize an expense?",
            "text": (
                "HisabDo helps organize business spending "
                "by assigning expenses to appropriate categories."
            ),
            "source": "Test fixture",
            "type": "faq",
            "version": "test-1",
            "verified": True,
        }
    ]

    docs_path = tmp_path / "faq_docs.json"
    docs_path.write_text(
        json.dumps(test_docs),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        faq_rag,
        "DOCS_PATH",
        docs_path,
    )

    # Pass the temporary path explicitly because the constructor's
    # default docs_path was evaluated when the class was defined.
    retriever = faq_rag.FaqRetriever(
        docs_path=docs_path,
    )

    matches = retriever.retrieve(
        "How do I categorize an expense?",
        top_k=1,
    )

    assert len(matches) == 1
    assert matches[0]["id"] == "faq-002"
    assert matches[0]["verified"] is True


def test_system_prompt_warns_against_inventing_product_details():
    """Ensure the system prompt discourages fabricated product details."""
    from src.financial_assistant.prompts import SYSTEM_PROMPT

    assert "invent" in SYSTEM_PROMPT.lower()

    assert (
        "hisabdo product" in SYSTEM_PROMPT.lower()
        or "api endpoints" in SYSTEM_PROMPT.lower()
    )
