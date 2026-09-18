"""Tests for get_llm_provider()'s per-module GROQ_API_KEY/LLM_PROVIDER
override (XICTEK_GROQ_API_KEY / XICTEK_LLM_PROVIDER), added so this
module's chat generation can run on a separate Groq key from HisabDo's
chatbot rather than always sharing one."""
import pytest

from src.xictek_website_assistant.llm_client import (
    GroqLLMProvider,
    MockLLMProvider,
    get_llm_provider,
)


@pytest.fixture(autouse=True)
def _clear_settings_caches():
    # get_settings()/get_xictek_settings() are lru_cache'd, so a Settings
    # instance built with this test's monkeypatched env vars would
    # otherwise leak into later tests (in this file or others) once
    # monkeypatch reverts the env — clear both before and after.
    from src.config import get_settings
    from src.xictek_website_assistant.config import get_xictek_settings

    get_settings.cache_clear()
    get_xictek_settings.cache_clear()
    yield
    get_settings.cache_clear()
    get_xictek_settings.cache_clear()


def test_defaults_to_mock_when_no_provider_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("XICTEK_LLM_PROVIDER", raising=False)
    assert isinstance(get_llm_provider(), MockLLMProvider)


def test_xictek_specific_key_takes_priority_over_shared_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "shared-hisabdo-key")
    monkeypatch.setenv("XICTEK_GROQ_API_KEY", "xictek-own-key")
    provider = get_llm_provider()
    assert isinstance(provider, GroqLLMProvider)
    assert provider._api_key == "xictek-own-key"


def test_falls_back_to_shared_key_when_no_xictek_specific_key_set(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "shared-hisabdo-key")
    monkeypatch.delenv("XICTEK_GROQ_API_KEY", raising=False)
    provider = get_llm_provider()
    assert isinstance(provider, GroqLLMProvider)
    assert provider._api_key == "shared-hisabdo-key"


def test_xictek_llm_provider_override_takes_priority(monkeypatch):
    # Shared LLM_PROVIDER says mock, but XICTEK_LLM_PROVIDER says groq —
    # the per-module override should win.
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("XICTEK_LLM_PROVIDER", "groq")
    monkeypatch.setenv("XICTEK_GROQ_API_KEY", "xictek-own-key")
    assert isinstance(get_llm_provider(), GroqLLMProvider)


def test_raises_clear_error_when_groq_selected_with_no_key_anywhere(monkeypatch):
    from src.errors import ServiceError

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("XICTEK_GROQ_API_KEY", raising=False)
    with pytest.raises(ServiceError):
        get_llm_provider()
