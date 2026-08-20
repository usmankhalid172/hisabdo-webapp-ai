"""

HisabDo AI Financial Assistant — LLM request/response layer.

Owner: Muhammad Hamza Nawaz
Day: 15 (initial implementation) -> Day 20 (finalize validation, error
handling, fallback behavior, and production-readiness notes)

Scope of this module (per Day 20 task description):
    - Define the LLM request flow
    - Validate request inputs
    - Validate returned responses where applicable
    - Handle API/model errors
    - Define timeout behavior
    - Define fallback behavior for unavailable/failed model responses

This module does NOT define:
    - The financial data retrieval / RAG layer (separate integration piece)
    - The FastAPI route layer (separate integration piece)
    - The prompt content itself (owned by Rameesha, Day 15 PR #4 — this
      module imports it from prompts.py so prompt changes don't require
      touching request-handling logic)

ASSUMPTION (flag for team lead review): built against an OpenAI-compatible
chat completions API. The LLM client is isolated in `_call_llm_api()` so
swapping providers (e.g. Gemini) only requires changing that one function.
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI, APITimeoutError, APIError, APIConnectionError

from .prompts import SYSTEM_PROMPT

logger = logging.getLogger("financial_assistant.llm_service")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LLMConfig:
    model: str = "gpt-4o-mini"
    timeout_seconds: float = 15.0
    max_retries: int = 1  # one retry on transient failure, then fallback
    max_input_chars: int = 1000
    min_input_chars: int = 1


DEFAULT_CONFIG = LLMConfig()


def _get_client() -> OpenAI:
    """
    Creates the API client. Reads the key from environment so credentials
    never get hardcoded or committed (per repo Security guidelines).
    """
    api_key = os.environ.get("FINANCIAL_ASSISTANT_LLM_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "FINANCIAL_ASSISTANT_LLM_API_KEY is not set in the environment."
        )
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class FinancialAssistantError(Exception):
    """Base class for all financial assistant LLM-layer errors."""


class LLMConfigurationError(FinancialAssistantError):
    """Raised when the service is misconfigured (e.g. missing API key)."""


class InvalidInputError(FinancialAssistantError):
    """Raised when the user's input fails validation before being sent."""


class InvalidResponseError(FinancialAssistantError):
    """Raised when the LLM response fails post-call validation."""


class LLMRequestError(FinancialAssistantError):
    """Raised when the LLM API call itself fails (timeout, API error, etc.)."""


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_user_input(user_question: str, config: LLMConfig = DEFAULT_CONFIG) -> str:
    """
    Validates and normalizes the user's question before it is sent to the
    LLM. Raises InvalidInputError on failure.

    Covers:
        - empty / whitespace-only input
        - excessively long input (cost + abuse control)
        - non-string input
    """
    if not isinstance(user_question, str):
        raise InvalidInputError("User question must be a string.")

    cleaned = user_question.strip()

    if len(cleaned) < config.min_input_chars:
        raise InvalidInputError("User question cannot be empty.")

    if len(cleaned) > config.max_input_chars:
        raise InvalidInputError(
            f"User question exceeds the {config.max_input_chars}-character limit."
        )

    return cleaned


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------

# Phrases that would indicate the model leaked its system prompt or internal
# instructions (see Rameesha's TC-19, prompt injection test case).
_LEAK_INDICATORS = (
    "you are the hisabdo ai financial assistant",
    "system prompt",
    "core responsibilities:",
)


def validate_llm_response(raw_response: str) -> str:
    """
    Validates the raw text returned by the LLM before it is passed back
    to the caller. Raises InvalidResponseError on failure.
    """
    if not raw_response or not raw_response.strip():
        raise InvalidResponseError("LLM returned an empty response.")

    lowered = raw_response.lower()
    for indicator in _LEAK_INDICATORS:
        if indicator in lowered:
            raise InvalidResponseError(
                "LLM response appears to leak internal system instructions."
            )

    return raw_response.strip()


# ---------------------------------------------------------------------------
# Fallback behavior
# ---------------------------------------------------------------------------

FALLBACK_MESSAGE = (
    "I'm having trouble answering that right now. Please try again in a "
    "moment. If the problem continues, contact support."
)


def get_fallback_response(reason: str) -> str:
    """
    Returns the user-facing fallback message. `reason` is logged internally
    for debugging but never shown to the user (avoids leaking internal
    error detail).
    """
    logger.warning("Falling back to default response. Reason: %s", reason)
    return FALLBACK_MESSAGE


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def _call_llm_api(
    user_question: str,
    config: LLMConfig,
    client: Optional[OpenAI] = None,
) -> str:
    """
    Makes a single call to the LLM API. Raises LLMRequestError on any
    failure (timeout, connection error, API error). No retry logic here —
    retries are handled by the caller so behavior is easy to reason about
    and test.
    """
    client = client or _get_client()

    try:
        response = client.chat.completions.create(
            model=config.model,
            timeout=config.timeout_seconds,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_question},
            ],
        )
    except APITimeoutError as exc:
        raise LLMRequestError(f"LLM request timed out after {config.timeout_seconds}s") from exc
    except APIConnectionError as exc:
        raise LLMRequestError("Could not connect to the LLM API.") from exc
    except APIError as exc:
        raise LLMRequestError(f"LLM API returned an error: {exc}") from exc

    choice = response.choices[0] if response.choices else None
    content = choice.message.content if choice and choice.message else None

    if content is None:
        raise LLMRequestError("LLM response contained no message content.")

    return content


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_financial_assistant_response(
    user_question: str,
    config: LLMConfig = DEFAULT_CONFIG,
    client: Optional[OpenAI] = None,
) -> str:
    """
    Full request flow: validate input -> call LLM (with retry) ->
    validate response -> return, or return the fallback message if
    anything along the way fails.

    This is the single function the integration/FastAPI layer should call.
    """
    try:
        cleaned_question = validate_user_input(user_question, config)
    except InvalidInputError as exc:
        # Bad input is a client-side problem, not a service failure —
        # surface it distinctly rather than masking it as a generic fallback.
        raise

    last_error: Optional[Exception] = None
    for attempt in range(config.max_retries + 1):
        try:
            raw_response = _call_llm_api(cleaned_question, config, client=client)
            return validate_llm_response(raw_response)
        except (LLMRequestError, InvalidResponseError) as exc:
            last_error = exc
            logger.warning(
                "Attempt %d/%d failed: %s",
                attempt + 1,
                config.max_retries + 1,
                exc,
            )
            if attempt < config.max_retries:
                time.sleep(1)  # brief backoff before retry
                continue

    return get_fallback_response(reason=str(last_error))