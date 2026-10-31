
"""
LLM provider abstraction.
"""
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
            f"Server error {resp.status_code}",
            request=resp.request,
            response=resp,
        )

        if attempt < _MAX_ATTEMPTS:
            time.sleep(_RETRY_DELAY_SECONDS)

    if last_exc is not None:
        raise last_exc

    raise RuntimeError("Request failed without an exception.")


class LLMProvider(ABC):
    @abstractmethod
    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        """Returns (reply_text, tokens_used_or_None)."""
        ...


class MockLLMProvider(LLMProvider):
    """Deterministic, offline provider used for testing."""

    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        if context:
            reply = (
                f"Here's what I found: {context.strip()} "
                f'(In response to: "{message.strip()}")'
            )
        else:
            reply = (
                "I don't have a specific answer for that in the current "
                "knowledge base yet, "
                f'but I understood you\'re asking: "{message.strip()}". '
                "Try rephrasing, or ask about a HisabDo feature directly."
            )

        return reply, len(reply.split())


class AnthropicLLMProvider(LLMProvider):
    """Calls the Anthropic Messages API."""

    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set",
                status_code=500,
            )
        self._api_key = settings.anthropic_api_key

    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        user_content = (
            f"Context:\n{context}\n\nUser question: {message}"
            if context
            else message
        )

        messages = [
            {"role": turn["role"], "content": turn["content"]}
            for turn in (history or [])
        ]
        messages.append({"role": "user", "content": user_content})

        resp = _post_with_retry(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 400,
                "system": SYSTEM_PROMPT,
                "messages": messages,
            },
            timeout=30,
        )

        data = resp.json()
        reply = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        tokens = data.get("usage", {}).get("output_tokens")

        return reply, tokens


class OpenAILLMProvider(LLMProvider):
    """Calls the OpenAI Chat Completions API."""

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=openai but OPENAI_API_KEY is not set",
                status_code=500,
            )
        self._api_key = settings.openai_api_key

    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        user_content = (
            f"Context:\n{context}\n\nUser question: {message}"
            if context
            else message
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(
            {"role": turn["role"], "content": turn["content"]}
            for turn in (history or [])
        )
        messages.append({"role": "user", "content": user_content})

        resp = _post_with_retry(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "content-type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": messages,
            },
            timeout=30,
        )

        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("completion_tokens")

        return reply, tokens

class GroqLLMProvider(LLMProvider):
    """Calls Groq's OpenAI-compatible Chat Completions API."""

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
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        user_content = (
            f"Context:\n{context}\n\nUser question: {message}"
            if context
            else message
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(
            {"role": turn["role"], "content": turn["content"]}
            for turn in (history or [])
        )
        messages.append({"role": "user", "content": user_content})

        resp = _post_with_retry(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "content-type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": messages,
            },
            timeout=30,
        )

        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("completion_tokens")

        return reply, tokens


def get_llm_provider() -> LLMProvider:
    settings = get_settings()

    if settings.llm_provider == "anthropic":
        return AnthropicLLMProvider(settings)
    if settings.llm_provider == "openai":
        return OpenAILLMProvider(settings)
    if settings.llm_provider == "groq":
        return GroqLLMProvider(settings)

    return MockLLMProvider()
