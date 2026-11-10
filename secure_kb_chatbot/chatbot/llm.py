"""Model clients behind one small protocol (``LLMClient.generate``).

* ``GeminiClient`` - Google Gemini (default; works with a free AI Studio key).
* ``ClaudeClient`` - Anthropic Claude.

``make_llm_client()`` picks one from ``CHATBOT_PROVIDER`` (``gemini`` | ``claude``).
The chat service only sees ``LLMResult``, so it can also be tested with a
fake client and no network access.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol

import anthropic

from .prompts import RESPONSE_SCHEMA

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


@dataclass
class LLMResult:
    stop_reason: str | None
    data: dict | None  # parsed structured output; None on refusal / bad output
    refusal_category: str | None = None
    request_id: str | None = None


class LLMClient(Protocol):
    def generate(self, system: list[dict], messages: list[dict]) -> LLMResult: ...


class LLMUnavailable(RuntimeError):
    """The API could not be reached or rejected the request; safe to show a generic error."""


class ClaudeClient:
    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
        client: anthropic.Anthropic | None = None,
    ) -> None:
        self.model = model or os.environ.get("CHATBOT_MODEL", DEFAULT_MODEL)
        self.effort = effort or os.environ.get("CHATBOT_EFFORT", "medium")
        self.client = client or anthropic.Anthropic()

    def generate(self, system: list[dict], messages: list[dict]) -> LLMResult:
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=messages,
                thinking={"type": "adaptive"},
                output_config={
                    "effort": self.effort,
                    "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA},
                },
                # If a safety classifier declines, re-run on Anthropic's
                # recommended fallback model instead of returning a refusal.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError as e:
            raise LLMUnavailable("The assistant is busy right now. Please try again shortly.") from e
        except anthropic.APIStatusError as e:
            raise LLMUnavailable(f"The assistant request failed (HTTP {e.status_code}).") from e
        except anthropic.APIConnectionError as e:
            raise LLMUnavailable("Could not reach the assistant service.") from e
        except TypeError as e:
            # The SDK resolves credentials lazily and raises TypeError when none are set.
            if "authentication" in str(e):
                raise LLMUnavailable("The AI assistant is not configured on this server.") from e
            raise

        result = LLMResult(stop_reason=response.stop_reason, data=None, request_id=getattr(response, "_request_id", None))
        if response.stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            result.refusal_category = getattr(details, "category", None)
            return result

        text = "".join(b.text for b in response.content if b.type == "text")
        try:
            data = json.loads(text)
            result.data = data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            result.data = None  # e.g. truncated at max_tokens; the service handles it
        return result


class GeminiClient:
    """Google Gemini via the official ``google-genai`` SDK.

    The API key is read from the ``GEMINI_API_KEY`` environment variable by
    the SDK itself; it never appears in code or config files.
    """

    # Finish/block reasons that mean the model declined for policy reasons.
    _POLICY_REASONS = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION", "JAILBREAK", "MODEL_ARMOR"}

    def __init__(self, model: str | None = None, client=None) -> None:
        from google import genai  # imported lazily so the Claude path doesn't need it

        self.model = model or os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self.client = client or genai.Client()  # raises if no key is configured

    def generate(self, system: list[dict], messages: list[dict]) -> LLMResult:
        from google.genai import errors, types

        contents = [
            types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part(text=m["content"])])
            for m in messages
        ]
        config = types.GenerateContentConfig(
            # Gemini takes one system instruction: rules followed by this turn's business context.
            system_instruction="\n\n".join(block["text"] for block in system),
            response_mime_type="application/json",
            response_json_schema=RESPONSE_SCHEMA,
            max_output_tokens=8192,
        )
        try:
            response = self.client.models.generate_content(model=self.model, contents=contents, config=config)
        except errors.ClientError as e:
            if e.code == 429:
                raise LLMUnavailable("The assistant's free-tier quota is used up for now. Please try again shortly.") from e
            if e.code in (400, 401, 403) and "key" in str(e).lower():
                raise LLMUnavailable("The AI assistant is not configured correctly (API key rejected).") from e
            raise LLMUnavailable(f"The assistant request failed (HTTP {e.code}).") from e
        except errors.APIError as e:
            raise LLMUnavailable(f"The assistant service is having problems (HTTP {e.code}).") from e
        except _TRANSPORT_ERRORS as e:
            raise LLMUnavailable("Could not reach the assistant service.") from e

        block = getattr(response.prompt_feedback, "block_reason", None) if response.prompt_feedback else None
        if block is not None:
            return LLMResult(stop_reason="refusal", data=None, refusal_category=_reason_name(block).lower())
        candidate = response.candidates[0] if response.candidates else None
        finish = _reason_name(candidate.finish_reason) if candidate and candidate.finish_reason else None
        if finish in self._POLICY_REASONS:
            return LLMResult(stop_reason="refusal", data=None, refusal_category=finish.lower())

        result = LLMResult(
            stop_reason="max_tokens" if finish == "MAX_TOKENS" else "end_turn",
            data=None,
            request_id=getattr(response, "response_id", None),
        )
        try:
            data = json.loads(response.text or "")
            result.data = data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            result.data = None  # e.g. truncated at max_output_tokens; the service handles it
        return result


def _reason_name(reason) -> str:
    return getattr(reason, "name", str(reason))


def _transport_errors() -> tuple[type[BaseException], ...]:
    found: list[type[BaseException]] = []
    for module in ("httpx", "httpx2"):  # google-genai may use either, depending on version
        try:
            found.append(__import__(module).TransportError)
        except (ImportError, AttributeError):
            pass
    return tuple(found) or (OSError,)


_TRANSPORT_ERRORS = _transport_errors()


def make_llm_client() -> LLMClient:
    """Build the configured client. Raises if its API key isn't set (the app reports 503)."""
    provider = os.environ.get("CHATBOT_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return GeminiClient()
    if provider == "claude":
        return ClaudeClient()
    raise ValueError(f"Unknown CHATBOT_PROVIDER {provider!r}; use 'gemini' or 'claude'")
