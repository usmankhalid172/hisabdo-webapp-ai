
import httpx
import pytest
from unittest.mock import MagicMock

from src.financial_assistant import llm_providers


def test_post_with_retry_retries_after_timeout(monkeypatch):
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.raise_for_status.return_value = None

    attempts = {"count": 0}

    def fake_post(url, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ReadTimeout("Simulated timeout")
        return success_response

    monkeypatch.setattr(llm_providers.httpx, "post", fake_post)
    monkeypatch.setattr(llm_providers.time, "sleep", lambda _: None)

    result = llm_providers._post_with_retry("https://example.com")

    assert result is success_response
    assert attempts["count"] == 2


def test_post_with_retry_raises_after_repeated_timeouts(monkeypatch):
    attempts = {"count": 0}

    def fake_post(url, **kwargs):
        attempts["count"] += 1
        raise httpx.ReadTimeout("Simulated timeout")

    monkeypatch.setattr(llm_providers.httpx, "post", fake_post)
    monkeypatch.setattr(llm_providers.time, "sleep", lambda _: None)

    with pytest.raises(httpx.ReadTimeout):
        llm_providers._post_with_retry("https://example.com")

    assert attempts["count"] == 2
