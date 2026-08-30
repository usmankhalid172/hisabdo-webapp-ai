"""
LLM provider abstraction.

Day 15 §2 flags the chatbot's model/provider (self-hosted vs external LLM
API) as undecided. Per the Day 16 continuity plan, the POC proceeds on a
documented assumption instead of blocking: `MockLLMProvider` is the default
so the service runs end-to-end with zero external credentials, and
`AnthropicLLMProvider` / `OpenAILLMProvider` are wired against the real
REST APIs so switching is a one-line config change (`LLM_PROVIDER=...`)
once a provider is chosen and a key is supplied — no code change needed
in `service.py`.
"""
from abc import ABC, abstractmethod

import httpx

from ..config import Settings, get_settings
from ..errors import ServiceError


class LLMProvider(ABC):
    @abstractmethod
    def generate_reply(self, message: str, context: str | None = None) -> tuple[str, int | None]:
        """Returns (reply_text, tokens_used_or_None)."""
        ...


class MockLLMProvider(LLMProvider):
    """Deterministic, offline provider used as the Day 16 POC default.

    Not a real language model — it composes a templated reply from the
    message and any retrieved context, which is enough to exercise the
    full request path (validation -> prompt building -> "model" call ->
    post-processing) and to keep tests deterministic.
    """

    def generate_reply(self, message: str, context: str | None = None) -> tuple[str, int | None]:
        if context:
            reply = (
                f"Based on HisabDo's docs: {context.strip()} "
                f"(In response to: \"{message.strip()}\")"
            )
        else:
            reply = (
                "I don't have a specific answer for that in the current knowledge base yet, "
                f"but I understood you're asking: \"{message.strip()}\". "
                "Try rephrasing, or ask about a HisabDo feature directly."
            )
        return reply, len(reply.split())


class AnthropicLLMProvider(LLMProvider):
    """Calls the real Anthropic Messages API. Requires ANTHROPIC_API_KEY."""

    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set",
                status_code=500,
            )
        self._api_key = settings.anthropic_api_key

    def generate_reply(self, message: str, context: str | None = None) -> tuple[str, int | None]:
        system = (
            "You are HisabDo's in-app financial assistant. Answer using only the "
            "provided context when given; be concise."
        )
        prompt = f"Context:\n{context}\n\nUser question: {message}" if context else message

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 400,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        reply = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        tokens = data.get("usage", {}).get("output_tokens")
        return reply, tokens


class OpenAILLMProvider(LLMProvider):
    """Calls the real OpenAI Chat Completions API. Requires OPENAI_API_KEY."""

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=openai but OPENAI_API_KEY is not set",
                status_code=500,
            )
        self._api_key = settings.openai_api_key

    def generate_reply(self, message: str, context: str | None = None) -> tuple[str, int | None]:
        prompt = f"Context:\n{context}\n\nUser question: {message}" if context else message

        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}", "content-type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are HisabDo's in-app financial assistant."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
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
    return MockLLMProvider()
