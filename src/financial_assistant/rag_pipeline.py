"""

HisabDo AI Financial Assistant — RAG context pipeline / prompt chain layer.

Owner: Muhammad Hamza Nawaz
Day: 23-24 — RAG Context Pipeline Setup

Scope of this module:
    - Accept retrieved context chunks (from whichever retriever the team
      settles on — see NOTE below) in a minimal, provider-agnostic shape.
    - Validate and normalize that context (drop malformed chunks, cap
      total size, order by relevance).
    - Format the context into a grounded user-prompt addition, so the
      question sent to the LLM includes the retrieved facts it should
      answer from.
    - Hand the assembled request off to llm_service.get_financial_assistant_response
      for everything downstream (validation, retry, error handling,
      fallback) — this module does not duplicate any of that.

This module does NOT define:
    - The retrieval algorithm itself (keyword search, vector search, etc.)
      — that is Ahmed Ali Ghori's / Faiza Asif's work
      (src/financial_assistant/rag.py, retriever.py, knowledge_base.py on
      Ahmed's branch; src/financial_assistant/rag/ package on Faiza's).
    - Which of those retrievers is canonical — deliberately not decided
      here (see NOTE).
    - The LLM request/response/error-handling flow (owned by
      llm_service.py, Day 15-22 — unchanged, reused as-is).

NOTE (flag for team lead / Umair review): as of Day 23-24, two independent
retriever implementations exist in this repo with no resolution on which
is canonical (flagged Day 17-22). Rather than build against either one and
risk being wired to the wrong base, this module accepts context as a
plain list of `ContextChunk` — any retriever can produce this shape by
mapping its own output to it in a few lines, so this pipeline works with
whichever retriever is eventually chosen without modification.

Context chunk shape expected: an object (or dict) with `text` (str) and
optionally `source` (str) and `score` (float) attributes/keys.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Union

from .llm_service import (
    LLMConfig,
    DEFAULT_CONFIG,
    InvalidInputError,
    get_financial_assistant_response,
)

logger = logging.getLogger("financial_assistant.rag_pipeline")


# ---------------------------------------------------------------------------
# Context chunk shape
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContextChunk:
    """
    Minimal, retriever-agnostic shape for a piece of retrieved context.

    Any retriever's own result type can be mapped into this with a small
    adapter, e.g.:
        ContextChunk(text=r.chunk.text, source=r.chunk.source, score=r.score)
    """
    text: str
    source: Optional[str] = None
    score: Optional[float] = None


RawChunk = Union[ContextChunk, dict]


@dataclass(frozen=True)
class PipelineConfig:
    max_context_chunks: int = 5
    max_context_chars: int = 3000  # total budget across all included chunks
    min_chunk_score: Optional[float] = None  # None = no score filtering


DEFAULT_PIPELINE_CONFIG = PipelineConfig()


class ContextFormattingError(Exception):
    """Raised when retrieved context cannot be safely formatted for the LLM."""


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def _to_context_chunk(raw: RawChunk) -> Optional[ContextChunk]:
    """
    Normalizes a single raw chunk (a ContextChunk or a dict) into a
    ContextChunk. Returns None for malformed input rather than raising —
    one bad chunk from a retriever should not fail the whole pipeline,
    it should just be dropped and logged.
    """
    if isinstance(raw, ContextChunk):
        text = raw.text
        source = raw.source
        score = raw.score
    elif isinstance(raw, dict):
        text = raw.get("text")
        source = raw.get("source")
        score = raw.get("score")
    else:
        logger.warning("Dropping context chunk of unsupported type: %r", type(raw))
        return None

    if not isinstance(text, str) or not text.strip():
        logger.warning("Dropping context chunk with empty/non-string text.")
        return None

    return ContextChunk(text=text.strip(), source=source, score=score)


# ---------------------------------------------------------------------------
# Pipeline: validate, rank, cap, format
# ---------------------------------------------------------------------------

def prepare_context(
    raw_chunks: Iterable[RawChunk],
    config: PipelineConfig = DEFAULT_PIPELINE_CONFIG,
) -> List[ContextChunk]:
    """
    Normalizes, filters, ranks, and caps retrieved chunks before they are
    formatted into a prompt. Never raises on malformed individual chunks
    (they are dropped) — only degrades gracefully to an empty list if
    everything is malformed, which the caller treats as "no context
    available" rather than an error.
    """
    normalized = [c for c in (_to_context_chunk(r) for r in raw_chunks) if c is not None]

    if config.min_chunk_score is not None:
        normalized = [
            c for c in normalized
            if c.score is None or c.score >= config.min_chunk_score
        ]

    # Highest-score first; chunks with no score keep their original
    # relative order and sort after scored chunks.
    normalized.sort(key=lambda c: (c.score is None, -(c.score or 0.0)))

    capped = normalized[: config.max_context_chunks]

    # Enforce a total character budget so a handful of long chunks can't
    # blow past the LLM's input limits or drive up cost unexpectedly.
    result: List[ContextChunk] = []
    running_total = 0
    for chunk in capped:
        if running_total + len(chunk.text) > config.max_context_chars:
            remaining = config.max_context_chars - running_total
            if remaining > 50:  # only keep a truncated chunk if it's still meaningfully long
                result.append(ContextChunk(
                    text=chunk.text[:remaining].rstrip() + "…",
                    source=chunk.source,
                    score=chunk.score,
                ))
            break
        result.append(chunk)
        running_total += len(chunk.text)

    return result


def format_context_block(chunks: List[ContextChunk]) -> str:
    """
    Formats prepared chunks into a labeled block to prepend to the user's
    question. Returns an empty string if there are no chunks — callers
    should treat that as "proceed ungrounded", not as an error.
    """
    if not chunks:
        return ""

    lines = ["Relevant financial data:"]
    for i, chunk in enumerate(chunks, start=1):
        label = f"[{i}]" + (f" ({chunk.source})" if chunk.source else "")
        lines.append(f"{label} {chunk.text}")

    return "\n".join(lines)


def build_grounded_question(user_question: str, chunks: List[ContextChunk]) -> str:
    """
    Combines the formatted context block with the user's question into
    the single string that gets sent as the user message. Keeping this
    as plain concatenation (not a separate message role) matches how
    llm_service.get_financial_assistant_response sends a single user
    message today — avoids touching that module's message-building logic.
    """
    context_block = format_context_block(chunks)
    if not context_block:
        return user_question
    return f"{context_block}\n\nQuestion: {user_question}"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_grounded_financial_assistant_response(
    user_question: str,
    raw_context_chunks: Iterable[RawChunk] = (),
    pipeline_config: PipelineConfig = DEFAULT_PIPELINE_CONFIG,
    llm_config: LLMConfig = DEFAULT_CONFIG,
    client=None,
) -> str:
    """
    Full grounded request flow: normalize/rank/cap retrieved context ->
    format it into the question -> hand off to the existing, unchanged
    llm_service request/response/error-handling flow.

    `raw_context_chunks` defaults to empty, so this function is a strict
    superset of `get_financial_assistant_response` — calling it with no
    context behaves identically to the ungrounded flow (same validation,
    same error handling, same fallback).
    """
    prepared = prepare_context(raw_context_chunks, config=pipeline_config)
    grounded_question = build_grounded_question(user_question, prepared)

    logger.info(
        "Grounded request: %d context chunk(s) attached (%d chars total).",
        len(prepared),
        sum(len(c.text) for c in prepared),
    )

    return get_financial_assistant_response(
        grounded_question, config=llm_config, client=client
    )