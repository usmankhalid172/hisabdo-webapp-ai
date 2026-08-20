"""Optional pluggable LLM provider for the AI Financial Assistant.

The assistant's primary flow is deterministic (intent detection -> backend
computation -> grounded response builder) so it works offline with no API key.
When ``OPENAI_API_KEY`` is set, responses may optionally be polished through an
LLM call (injected with grounded facts/context). Failures or missing keys fall
back to the deterministic response, never blocking the flow.

This isolates the external-API dependency as an *optional* enhancement: the
absence of an API key is a soft dependency, not a blocker.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional


def llm_available() -> bool:
    """True if an OpenAI-compatible API key is configured."""
    return bool(os.environ.get("OPENAI_API_KEY") or
                os.environ.get("OPENAI_COMPAT_BASE_URL"))


def _api_key() -> Optional[str]:
    return os.environ.get("OPENAI_API_KEY")


def _base_url() -> str:
    return os.environ.get("OPENAI_COMPAT_BASE_URL", "https://api.openai.com/v1")


class LLMUnavailableError(RuntimeError):
    """Raised when the LLM provider cannot be used."""


def complete_with_llm(question: str, system_prompt: str, user_prompt: str,
                      model: str = "gpt-4o-mini", max_tokens: int = 300,
                      temperature: float = 0.2) -> str:
    """Call an OpenAI-compatible chat completion API.

    Raises :class:`LLMUnavailableError` when no key is configured or the call
    fails, so callers can fall back to the deterministic response.
    """
    key = _api_key()
    if not key:
        raise LLMUnavailableError("OPENAI_API_KEY not configured")

    endpoint = _base_url().rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint, data=data,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()