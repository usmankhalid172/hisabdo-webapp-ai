from src.financial_assistant.service import handle_chat
from src.schemas import ChatbotRequest


def test_own_financial_data_query_uses_backend_not_rag():
    req = ChatbotRequest(
        user_id="user-1", message="What is my balance right now?", conversation_id="c1"
    )
    resp = handle_chat(req)
    assert resp.source == "backend_financial_api"
    assert resp.intent == "own_financial_data"


def test_product_faq_query_uses_rag():
    req = ChatbotRequest(
        user_id="user-1",
        message="How does automatic expense categorization work?",
        conversation_id="c2",
    )
    resp = handle_chat(req)
    assert resp.source == "rag"
    assert resp.intent == "product_faq"


def test_unrelated_query_returns_safe_empty_retrieval_response():
    req = ChatbotRequest(
        user_id="user-1", message="asdkjhasd unrelated gibberish zzz", conversation_id="c3"
    )
    resp = handle_chat(req)
    assert resp.source == "rag_empty"
    assert resp.intent == "no_verified_source"
    assert resp.tokens_used == 0


def test_chatbot_endpoint_returns_valid_shape(client, auth_headers):
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
    """service.py must forward request.history into generate_reply —
    regression guard for the bug where history was silently dropped."""
    captured = {}

    class SpyProvider:
        def generate_reply(self, message, context=None, history=None):
            captured["history"] = history
            captured["message"] = message
            return "reply", 10

    monkeypatch.setattr(
        "src.financial_assistant.service.get_llm_provider",
        lambda: SpyProvider(),
    )

    from src.financial_assistant.service import handle_chat
    from src.schemas import ChatbotRequest

    history = [
        {"role": "user", "content": "How do I categorize an expense?"},
        {"role": "assistant", "content": "Rule-based + ML model."},
    ]
    request = ChatbotRequest(
        user_id="test-user",
        message="How do I categorize an expense?",
        conversation_id="test-convo",
        history=history,
    )
    handle_chat(request)

    assert captured["history"] == history


def test_mock_provider_does_not_mislabel_financial_data_as_docs():
    """Regression guard for the bug where backend_financial_api context
    was described as 'HisabDo's docs' in the reply text."""
    from src.financial_assistant.llm_providers import MockLLMProvider

    provider = MockLLMProvider()
    reply, _ = provider.generate_reply(
        "What is my balance?",
        context="Balance: 100 PKR.",
    )
    assert "docs" not in reply.lower()


def test_weak_rag_match_returns_no_verified_source_instead_of_wrong_answer():
    """Regression guard: a query with no good FAQ match (e.g. paraphrased
    export question, which previously top-matched the unrelated
    'is my data used to train the model' FAQ at a low score) must fall
    to the safe empty retrieval response rather than returning a confidently
    wrong RAG answer or an ungrounded general response. See RELEVANCE_THRESHOLD in faq_rag.py."""
    from src.financial_assistant.faq_rag import get_retriever

    matches = get_retriever().retrieve(
        "How can I get my spending data out of the app?", top_k=1
    )
    assert matches == []


def test_strong_rag_match_still_retrieves():
    """Regression guard: raising RELEVANCE_THRESHOLD must not break
    legitimate high-confidence matches."""
    from src.financial_assistant.faq_rag import get_retriever

    matches = get_retriever().retrieve("How do I categorize an expense?", top_k=1)
    assert len(matches) == 1
    assert matches[0]["id"] == "faq-002"


def test_system_prompt_warns_against_inventing_product_details():
    """Regression guard: SYSTEM_PROMPT must explicitly instruct against
    fabricating specific HisabDo product/API details when ungrounded.
    Found via live testing: Groq confidently invented a full fake
    /categorize-batch API spec (endpoint, fields, example JSON) for a
    feature marked "(Planned)" in the actual API docs, before this rule
    was added."""
    from src.financial_assistant.prompts import SYSTEM_PROMPT

    assert "invent" in SYSTEM_PROMPT.lower()
    assert "hisabdo product" in SYSTEM_PROMPT.lower() or "api endpoints" in SYSTEM_PROMPT.lower()

def test_rag_provider_failure_returns_safe_response(monkeypatch):
    class FailingProvider:
        def generate_reply(self, *args, **kwargs):
            raise RuntimeError("sensitive provider error")

    monkeypatch.setattr(
        "src.financial_assistant.service.get_llm_provider",
        lambda: FailingProvider(),
    )

    request = ChatbotRequest(
        user_id="test-user",
        message="How do I categorize an expense?",
        conversation_id="provider-failure",
    )
    response = handle_chat(request)

    assert response.source == "provider_error"
    assert response.intent == "provider_unavailable"
    assert response.tokens_used == 0
    assert "try again later" in response.reply.lower()


def test_index_refresh_failure_keeps_previous_index(tmp_path):
    from src.financial_assistant.faq_rag import FaqRetriever

    docs = tmp_path / "faq.json"
    docs.write_text(
        '[{"id":"test-1","title":"Expense help","text":"How to categorize an expense"}]',
        encoding="utf-8",
    )

    retriever = FaqRetriever(docs)
    docs.write_text("invalid json", encoding="utf-8")

    assert retriever.refresh() is False
    assert retriever.retrieve("How to categorize an expense")
