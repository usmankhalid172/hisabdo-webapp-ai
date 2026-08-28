"""
Task 26 - Chatbot/RAG backend integration robustness tests.

These guard the core requirement: fetching document contexts (RAG) or any
other external dependency (application backend, LLM provider) must never
crash the backend. On failure the service layer must degrade to a safe,
user-facing reply with a distinct ``source`` rather than raise (which would
surface as a 500 to the caller).
"""
from src.financial_assistant import service as service_mod
from src.financial_assistant.rag import FaqRetriever
from src.schemas import ChatbotRequest


def _req(message="What is a cash flow statement?", user_id="user-t1"):
    return ChatbotRequest(
        user_id=user_id,
        message=message,
        conversation_id="conv-t1",
    )


# ------------------------------------------------------------------ #
# Document-context (RAG) fetch failure -> must NOT crash
# ------------------------------------------------------------------ #
def test_scenario_rag_retriever_failure_falls_back_without_crash(monkeypatch):
    def boom(query, top_k=1):
        raise RuntimeError("kb doc fetch failed")

    monkeypatch.setattr(service_mod, "get_retriever", lambda: type(
        "Bad", (), {"retrieve": boom})())
    resp = service_mod.handle_chat(_req())
    assert resp.source == "llm_general"  # degraded, not a 500
    assert resp.reply  # non-empty user-facing reply


def test_scenario_empty_corpus_falls_back_without_crash(tmp_path):
    # A knowledge-base JSON that exists but is malformed/empty must not crash.
    bad_file = tmp_path / "faq_docs.json"
    bad_file.write_text("this is { not valid json", encoding="utf-8")
    retriever = FaqRetriever(docs_path=bad_file)
    assert retriever.loaded is False
    assert retriever.retrieve("How do I export my expenses?", top_k=1) == []


def test_scenario_missing_corpus_falls_back_without_crash(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    retriever = FaqRetriever(docs_path=missing)
    assert retriever.loaded is False
    assert retriever.retrieve("anything", top_k=1) == []


# ------------------------------------------------------------------ #
# Backend financial API failure -> must NOT crash
# ------------------------------------------------------------------ #
def test_scenario_backend_api_failure_surfaces_backend_unavailable(monkeypatch):
    class FailingBackend:
        def get_user_financial_summary(self, user_id):
            raise ConnectionError("backend unreachable")

    monkeypatch.setattr(service_mod, "get_backend_client",
                        lambda: FailingBackend())
    resp = service_mod.handle_chat(_req(message="What is my balance?"))
    assert resp.intent == "own_financial_data"
    assert resp.source == "backend_unavailable"
    assert resp.reply  # user-safe fallback, not a crash


# ------------------------------------------------------------------ #
# LLM provider failure -> must NOT crash
# ------------------------------------------------------------------ #
def test_scenario_llm_provider_failure_falls_back_without_crash(monkeypatch):
    class FailingProvider:
        def generate_reply(self, message, context=None):
            raise RuntimeError("llm down")

    monkeypatch.setattr(service_mod, "get_llm_provider",
                        lambda: FailingProvider())
    resp = service_mod.handle_chat(_req())
    assert resp.reply  # fallback message returned
    assert resp.source in ("rag", "llm_general")
    assert resp.reply == service_mod.FALLBACK_REPLY


# ------------------------------------------------------------------ #
# Live endpoint (TestClient) contract for the graceful paths
# ------------------------------------------------------------------ #
def test_scenario_live_endpoint_returns_graceful_response(client, auth_headers):
    resp = client.post(
        "/api/v1/chatbot",
        json=_req("What is a cash flow statement?").model_dump(),
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] in ("rag", "llm_general")
    assert body["reply"]


def test_scenario_live_endpoint_empty_message_is_422_not_crash(client, auth_headers):
    resp = client.post(
        "/api/v1/chatbot",
        json={"user_id": "u", "message": "  ", "conversation_id": "c"},
        headers=auth_headers,
    )
    assert resp.status_code == 200  # whitespace message passes schema
    # An entirely empty message string is rejected by Pydantic (min_length=1).
    empty_resp = client.post(
        "/api/v1/chatbot",
        json={"user_id": "u", "message": "", "conversation_id": "c"},
        headers=auth_headers,
    )
    assert empty_resp.status_code == 422
