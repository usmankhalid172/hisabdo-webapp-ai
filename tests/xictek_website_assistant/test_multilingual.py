"""Tests for multilingual support (English/Urdu/Hindi/Arabic), added per
the team lead's request after reviewing the initial build."""
from src.xictek_website_assistant.config import get_xictek_settings
from src.xictek_website_assistant.prompts import SYSTEM_PROMPT


def test_default_embedding_model_is_multilingual():
    settings = get_xictek_settings()
    assert "multilingual" in settings.embedding_model


def test_system_prompt_instructs_multilingual_response():
    lower = SYSTEM_PROMPT.lower()
    assert "urdu" in lower
    assert "hindi" in lower
    assert "arabic" in lower
    assert "english" in lower


def test_chat_endpoint_accepts_non_english_message(client, auth_headers):
    # Guardrails/schema should be script-agnostic (they check length and
    # English-language injection phrases, not a message's language) --
    # a message in Urdu should flow through exactly like an English one.
    urdu_message = "زکٹیک کیا خدمات پیش کرتا ہے؟"  # "What services does XICTEK offer?"
    resp = client.post(
        "/api/v1/xictek/chat",
        headers=auth_headers,
        json={"message": urdu_message, "conversation_id": "multilingual-test"},
    )
    assert resp.status_code == 200
    assert resp.json()["intent"] in {"answered", "general"}


def test_chat_endpoint_accepts_arabic_message(client, auth_headers):
    arabic_message = "ما هي الخدمات التي تقدمها XICTEK؟"
    resp = client.post(
        "/api/v1/xictek/chat",
        headers=auth_headers,
        json={"message": arabic_message, "conversation_id": "multilingual-test-ar"},
    )
    assert resp.status_code == 200


def test_chat_endpoint_accepts_hindi_message(client, auth_headers):
    hindi_message = "XICTEK क्या सेवाएं प्रदान करता है?"
    resp = client.post(
        "/api/v1/xictek/chat",
        headers=auth_headers,
        json={"message": hindi_message, "conversation_id": "multilingual-test-hi"},
    )
    assert resp.status_code == 200
