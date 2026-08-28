"""
Task 27 - Chatbot/RAG payload formatting finalization & backend-to-vector
service-layer optimization tests.

Covers:
  - finalized chatbot response payload (user_id echo, model, matched_context)
  - typed conversation history in ChatbotRequest (validation of role/content)
  - backend client singleton (backend-to-service layer optimization)
  - retriever (vector service layer) singleton + warm reuse optimization
"""
import pytest
from pydantic import ValidationError

from src.financial_assistant.rag import get_retriever
from src.financial_assistant.service import handle_chat
from src.integration.backend_client import get_backend_client
from src.schemas import ChatbotRequest


def _req(message="What is a cash flow statement?", user_id="user-27"):
    return ChatbotRequest(
        user_id=user_id,
        message=message,
        conversation_id="conv-27",
    )


# ------------------------------------------------------------------ #
# Payload formatting: self-describing response
# ------------------------------------------------------------------ #
def test_rag_reply_echoes_user_id_model_and_matched_context():
    resp = handle_chat(_req())
    assert resp.source == "rag"
    assert resp.user_id == "user-27"
    assert resp.conversation_id == "conv-27"
    assert resp.model == "mock-llm"  # surfaced for demo visibility
    assert resp.matched_context  # retrieved doc title surfaced when source==rag


def test_general_reply_still_sets_user_id_model_no_context():
    resp = handle_chat(_req(message="asdkjhasd gibberish zzz"))
    assert resp.source == "llm_general"
    assert resp.user_id == "user-27"
    assert resp.model == "mock-llm"
    assert resp.matched_context is None


def test_own_financial_data_reply_echoes_user_id_and_model():
    resp = handle_chat(_req(message="What is my balance?"))
    assert resp.source == "backend_financial_api"
    assert resp.user_id == "user-27"
    assert resp.model == "mock-llm"
    assert resp.matched_context is None


# ------------------------------------------------------------------ #
# Payload formatting: typed conversation history (validation)
# ------------------------------------------------------------------ #
def test_valid_history_entries_are_accepted():
    req = _req()
    req.history = [
        {"role": "user", "content": "What is my balance?"},
        {"role": "assistant", "content": "Your balance is PKR 45,230.50."},
    ]
    resp = handle_chat(req)
    assert resp.reply


def test_invalid_history_role_is_rejected():
    with pytest.raises(ValidationError):
        ChatbotRequest(
            user_id="u", message="hi", conversation_id="c",
            history=[{"role": "system", "content": "you are..."}],
        )


def test_empty_history_content_is_rejected():
    with pytest.raises(ValidationError):
        ChatbotRequest(
            user_id="u", message="hi", conversation_id="c",
            history=[{"role": "user", "content": ""}],
        )


# ------------------------------------------------------------------ #
# Backend-to-vector service-layer optimization: singletons + warm reuse
# ------------------------------------------------------------------ #
def test_backend_client_is_a_process_wide_singleton():
    assert get_backend_client() is get_backend_client()


def test_retriever_is_a_process_wide_singleton():
    assert get_retriever() is get_retriever()


def test_retriever_matrix_is_built_once_and_reused():
    # The vectorizer/matrix is built at construction; repeated retrieves only
    # transform the query, so subsequent calls are cheap (no re-vectorization).
    r = get_retriever()
    first = r.retrieve("How do I export my expenses?", top_k=1)
    second = r.retrieve("How do I export my expenses?", top_k=1)
    assert first == second  # deterministic, no rebuild between calls
