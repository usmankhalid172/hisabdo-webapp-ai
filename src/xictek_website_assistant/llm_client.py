"""
LLM provider for the XICTEK website assistant.

Deliberately its own small provider (not importing
`financial_assistant.llm_providers`) so this module stays a self-contained,
portable unit per the plan — no cross-import into HisabDo's module, no
shared blast radius if either module's provider logic changes. It follows
the same shape (Mock default, real provider needs a key, retry on
transient 5xx) so it's a familiar pattern to anyone who's read that file.

Reuses `src.config.get_settings()` for `GROQ_API_KEY` / `LLM_PROVIDER`
rather than duplicating those — they're genuinely shared, service-wide
secrets, not XICTEK-specific config (see config.py's docstring).
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod

import httpx

from ..config import Settings, get_settings
from ..errors import ServiceError
from .prompts import SYSTEM_PROMPT

_RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
_MAX_ATTEMPTS = 2
_RETRY_DELAY_SECONDS = 1.5


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
        return reply, len(reply.split())


class GroqLLMProvider(LLMProvider):
    """Calls Groq's OpenAI-compatible Chat Completions API. Requires GROQ_API_KEY."""

    def __init__(self, settings: Settings):
        if not settings.groq_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=groq but GROQ_API_KEY is not set",
                status_code=500,
            )
        self._api_key = settings.groq_api_key

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
        tokens = data.get("usage", {}).get("completion_tokens")
        return reply, tokens


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "groq":
        return GroqLLMProvider(settings)
    return MockLLMProvider()
