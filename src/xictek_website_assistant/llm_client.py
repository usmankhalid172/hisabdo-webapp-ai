"""
LLM provider for the XICTEK website assistant.

Deliberately its own small provider (not importing
`financial_assistant.llm_providers`) so this module stays a self-contained,
portable unit per the plan — no cross-import into HisabDo's module, no
shared blast radius if either module's provider logic changes. It follows
the same shape (Mock default, real provider needs a key, retry on
transient 5xx) so it's a familiar pattern to anyone who's read that file.

Reuses `src.config.get_settings()` for `GROQ_API_KEY` / `LLM_PROVIDER` by
default, since they're normally shared, service-wide secrets — but either
can be overridden per-module via `XICTEK_GROQ_API_KEY` / `XICTEK_LLM_PROVIDER`
(see config.py) so this module's chat generation can run on its own Groq
key, independent of HisabDo's chatbot.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod

import httpx

from ..config import get_settings
from ..errors import ServiceError
from .config import get_xictek_settings
from .prompts import SYSTEM_PROMPT

_RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
_MAX_ATTEMPTS = 2
_RETRY_DELAY_SECONDS = 1.5


def _token_count(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _post_with_retry(url: str, **kwargs) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            resp = httpx.post(url, **kwargs)
        except httpx.TimeoutException as exc:
            last_exc = exc
            if attempt < _MAX_ATTEMPTS:
                time.sleep(_RETRY_DELAY_SECONDS)
            continue

        if resp.status_code not in _RETRYABLE_STATUS_CODES:
            resp.raise_for_status()
            return resp
        last_exc = httpx.HTTPStatusError(
            f"Server error {resp.status_code}", request=resp.request, response=resp
        )
        if attempt < _MAX_ATTEMPTS:
            time.sleep(_RETRY_DELAY_SECONDS)
    raise last_exc


class LLMProvider(ABC):
    provider_name = "unknown"

    def __init__(self) -> None:
        self._usage_metrics: dict[str, int | str | None] = {}

    @property
    def usage_metrics(self) -> dict[str, int | str | None]:
        return self._usage_metrics.copy()

    @abstractmethod
    def generate_reply(
        self,
        message: str,
        context: str | None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        """Returns (reply_text, tokens_used_or_None)."""
        ...


class MockLLMProvider(LLMProvider):
    """Deterministic, offline provider — default until GROQ_API_KEY / LLM_PROVIDER
    is configured, so the endpoint is demoable via Swagger with zero setup."""

    provider_name = "mock"

    def __init__(self) -> None:
        super().__init__()

    def generate_reply(
        self,
        message: str,
        context: str | None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        if context:
            reply = (
                f"Based on XICTEK's website content: {context.strip()} "
                f"(In response to: \"{message.strip()}\")"
            )
        else:
            reply = (
                "I don't have that in the current XICTEK knowledge base yet. "
                "Try rephrasing, or ask about our services, technologies, HisabDo, careers, or blog."
            )
        completion_tokens = len(reply.split())
        self._usage_metrics = {
            "input_tokens": None,
            "completion_tokens": completion_tokens,
            "total_tokens": None,
            "usage_basis": "mock_word_estimate",
        }
        return reply, completion_tokens


class GroqLLMProvider(LLMProvider):
    """Calls Groq's OpenAI-compatible Chat Completions API. Requires an
    API key — either XICTEK_GROQ_API_KEY (this module's own key, if set)
    or the shared GROQ_API_KEY as a fallback."""

    provider_name = "groq"

    def __init__(self, api_key: str):
        super().__init__()
        self._api_key = api_key

    def generate_reply(
        self,
        message: str,
        context: str | None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        user_content = f"Context:\n{context}\n\nVisitor question: {message}" if context else message

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(
            {"role": turn["role"], "content": turn["content"]}
            for turn in (history or [])
        )
        messages.append({"role": "user", "content": user_content})

        resp = _post_with_retry(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}", "content-type": "application/json"},
            json={"model": "openai/gpt-oss-120b", "messages": messages},
            timeout=30,
        )
        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        self._usage_metrics = {
            "input_tokens": _token_count(usage.get("prompt_tokens")),
            "completion_tokens": _token_count(usage.get("completion_tokens")),
            "total_tokens": _token_count(usage.get("total_tokens")),
            "usage_basis": "provider_reported" if usage else "unavailable",
        }
        tokens = _token_count(usage.get("completion_tokens"))
        return reply, tokens


import logging as _logging

_provider_logger = _logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    xictek_settings = get_xictek_settings()

    def _clean(value) -> str:
        # Tolerate a hand-typed dashboard value such as ' Groq ' or '"groq"'.
        return str(value or "").strip().strip("\"'").lower()

    xictek_choice = _clean(xictek_settings.llm_provider)
    shared_choice = _clean(settings.llm_provider)
    # Use Groq if EITHER the XICTEK-specific or the shared (HisabDo) setting asks
    # for it, so XICTEK works wherever HisabDo's chatbot already works.
    provider = "groq" if "groq" in (xictek_choice, shared_choice) else (xictek_choice or shared_choice)
    if provider == "groq":
        api_key = xictek_settings.groq_api_key or settings.groq_api_key
        if not api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=groq but neither XICTEK_GROQ_API_KEY nor GROQ_API_KEY is set",
                status_code=500,
            )
        return GroqLLMProvider(api_key)
    _provider_logger.warning(
        "llm_provider_is_mock: XICTEK_LLM_PROVIDER=%r LLM_PROVIDER=%r -> using MockLLMProvider",
        xictek_settings.llm_provider,
        settings.llm_provider,
    )
    return MockLLMProvider()
