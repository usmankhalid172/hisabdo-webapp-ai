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


def test_unrelated_query_falls_back_to_general():
    req = ChatbotRequest(
        user_id="user-1", message="asdkjhasd unrelated gibberish zzz", conversation_id="c3"
    )
    resp = handle_chat(req)
    assert resp.source == "llm_general"
    assert resp.intent == "general"


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
