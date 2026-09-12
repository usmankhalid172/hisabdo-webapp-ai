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
import time
from abc import ABC, abstractmethod

import httpx

from ..config import Settings, get_settings
from ..errors import ServiceError
from .prompts import SYSTEM_PROMPT

# Real LLM APIs occasionally return transient 5xx errors under load (seen in
# practice: Gemini 503s). A single retry with a short backoff turns a
# transient blip into a successful response instead of a hard user-facing
# failure; if it fails twice, that's a genuine outage worth surfacing.
_RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
_MAX_ATTEMPTS = 2
_RETRY_DELAY_SECONDS = 1.5


def _post_with_retry(url: str, **kwargs) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            resp = httpx.post(url, **kwargs)
        except httpx.TimeoutException as exc:
            # A hung/slow provider response, not a status code — retry the
            # same as a 5xx, since a second attempt commonly succeeds.
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
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        """Returns (reply_text, tokens_used_or_None).

        `history` is prior conversation turns, oldest first, each shaped
        like {"role": "user"|"assistant", "content": str}.
        """
        ...


class MockLLMProvider(LLMProvider):
    """Deterministic, offline provider used as the Day 16 POC default.

    Not a real language model — it composes a templated reply from the
    message and any retrieved context, which is enough to exercise the
    full request path (validation -> prompt building -> "model" call ->
    post-processing) and to keep tests deterministic.

    Deliberately ignores `history`: it has no real language understanding
    to make context-aware use of prior turns, so accepting-and-ignoring is
    the honest behavior here (unlike the real providers below).
    """

    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        if context:
            # Was "Based on HisabDo's docs: ..." — wrong when context came
            # from the backend financial API (a user's live balance is not
            # a "doc"). Neutral phrasing works regardless of provenance.
            reply = (
                f"Here's what I found: {context.strip()} "
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

    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        user_content = f"Context:\n{context}\n\nUser question: {message}" if context else message

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

    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        user_content = f"Context:\n{context}\n\nUser question: {message}" if context else message

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(
            {"role": turn["role"], "content": turn["content"]}
            for turn in (history or [])
        )
        messages.append({"role": "user", "content": user_content})

        resp = _post_with_retry(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}", "content-type": "application/json"},
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


class GeminiLLMProvider(LLMProvider):
    """Calls the real Google Gemini API. Requires GEMINI_API_KEY."""

    def __init__(self, settings: Settings):
        if not settings.gemini_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=gemini but GEMINI_API_KEY is not set",
                status_code=500,
            )
        self._api_key = settings.gemini_api_key

    def generate_reply(
        self,
        message: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> tuple[str, int | None]:
        user_content = f"Context:\n{context}\n\nUser question: {message}" if context else message

        # Gemini uses "user"/"model" roles (not "assistant"), and wraps each
        # turn's text in a "parts" list rather than a flat "content" string.
        contents = [
            {
                "role": "model" if turn["role"] == "assistant" else "user",
                "parts": [{"text": turn["content"]}],
            }
            for turn in (history or [])
        ]
        contents.append({"role": "user", "parts": [{"text": user_content}]})

        resp = _post_with_retry(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent",
            headers={"content-type": "application/json"},
            params={"key": self._api_key},
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents,
            },
            timeout=30,
        )
        data = resp.json()
        reply = "".join(
            part.get("text", "")
            for part in data["candidates"][0]["content"]["parts"]
        )
        tokens = data.get("usageMetadata", {}).get("candidatesTokenCount")
        return reply, tokens


class GroqLLMProvider(LLMProvider):
    """Calls Groq's OpenAI-compatible Chat Completions API. Requires GROQ_API_KEY.

    Groq hosts open models (not its own); some of them (e.g. gpt-oss) return
    an extra "reasoning" field alongside "content" in the response message.
    We only read "content" — the final answer — same as OpenAILLMProvider.
    """

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
        user_content = f"Context:\n{context}\n\nUser question: {message}" if context else message

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(
            {"role": turn["role"], "content": turn["content"]}
            for turn in (history or [])
        )
        messages.append({"role": "user", "content": user_content})

        resp = _post_with_retry(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}", "content-type": "application/json"},
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
    if settings.llm_provider == "gemini":
        return GeminiLLMProvider(settings)
    if settings.llm_provider == "groq":
        return GroqLLMProvider(settings)
    return MockLLMProvider()
