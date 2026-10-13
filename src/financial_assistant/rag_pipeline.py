
"""
HisabDo AI Financial Assistant — RAG context pipeline.

Responsibilities:
- Normalize and validate retrieved context.
- Rank and limit context chunks.
- Build a grounded prompt with source attribution.
- Send grounded questions to the existing LLM service.
- Provide a separate entry point for HisabDo FAQ retrieval.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import Iterable, Optional, Union

from .llm_service import (
    LLMConfig,
    DEFAULT_CONFIG,
    get_financial_assistant_response,
)

logger = logging.getLogger("financial_assistant.rag_pipeline")


@dataclass(frozen=True)
class ContextChunk:
    """A normalized piece of retrieved context."""

    text: str
    source: Optional[str] = None
    score: Optional[float] = None


RawChunk = Union[ContextChunk, dict]


@dataclass(frozen=True)
class PipelineConfig:
    max_context_chunks: int = 5
    max_context_chars: int = 3000
    min_chunk_score: Optional[float] = None


DEFAULT_PIPELINE_CONFIG = PipelineConfig()


class ContextFormattingError(Exception):
    """Raised when retrieved context cannot be safely formatted."""


def _to_context_chunk(raw: RawChunk) -> Optional[ContextChunk]:
    """Convert a supported input into a validated context chunk."""

    if isinstance(raw, ContextChunk):
        text = raw.text
        source = raw.source
        score = raw.score

    elif isinstance(raw, dict):
        text = raw.get("text")
        source = raw.get("source")
        score = raw.get("score")

    else:
        logger.warning(
            "Ignoring unsupported context type: %r",
            type(raw),
        )
        return None

    if not isinstance(text, str) or not text.strip():
        logger.warning("Ignoring context with empty or invalid text.")
        return None

    if source is not None and not isinstance(source, str):
        source = None

    if isinstance(source, str):
        source = source.strip() or None

    if score is not None:
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = None

    return ContextChunk(
        text=text.strip(),
        source=source,
        score=score,
    )


def prepare_context(
    raw_chunks: Iterable[RawChunk],
    config: PipelineConfig = DEFAULT_PIPELINE_CONFIG,
) -> list[ContextChunk]:
    """Validate, rank, and limit retrieved context."""

    if config.max_context_chunks < 1 or config.max_context_chars < 1:
        return []

    normalized = [
        chunk
        for chunk in (_to_context_chunk(raw) for raw in raw_chunks)
        if chunk is not None
    ]

    if config.min_chunk_score is not None:
        normalized = [
            chunk
            for chunk in normalized
            if chunk.score is not None
            and chunk.score >= config.min_chunk_score
        ]

    normalized.sort(
        key=lambda chunk: (
            chunk.score is None,
            -(chunk.score if chunk.score is not None else 0.0),
        )
    )

    selected: list[ContextChunk] = []
    remaining = config.max_context_chars

    for chunk in normalized:
        if len(selected) >= config.max_context_chunks or remaining <= 0:
            break

        if len(chunk.text) <= remaining:
            selected.append(chunk)
            remaining -= len(chunk.text)

        elif remaining > 50:
            selected.append(
                ContextChunk(
                    text=chunk.text[: remaining - 1].rstrip() + "…",
                    source=chunk.source,
                    score=chunk.score,
                )
            )
            break

    return selected


def format_context_block(chunks: list[ContextChunk]) -> str:
    """Format context using the existing financial-data heading."""

    if not chunks:
        return ""

    lines = ["Relevant financial data:"]

    for index, chunk in enumerate(chunks, start=1):
        if chunk.source:
            lines.append(
                f"[{index}] ({chunk.source}) {chunk.text}"
            )
        else:
            lines.append(f"[{index}] {chunk.text}")

    return "\n".join(lines)


def build_grounded_question(
    user_question: str,
    chunks: list[ContextChunk],
) -> str:
    """Combine retrieved information with the user's question."""

    context_block = format_context_block(chunks)

    if not context_block:
        return user_question

    return (
        f"{context_block}\n\n"
        f"Question: {user_question.strip()}"
    )


def get_grounded_financial_assistant_response(
    user_question: str,
    raw_context_chunks: Iterable[RawChunk] = (),
    pipeline_config: PipelineConfig = DEFAULT_PIPELINE_CONFIG,
    llm_config: LLMConfig = DEFAULT_CONFIG,
    client=None,
) -> str:
    """Generate a response using available context."""

    if not isinstance(user_question, str) or not user_question.strip():
        return "Please enter a valid question."

    question = user_question.strip()

    prepared = prepare_context(
        raw_context_chunks,
        config=pipeline_config,
    )

    # Preserve the existing LLM-service behavior when no context
    # is supplied. The caller remains responsible for deciding
    # whether an ungrounded/general answer is appropriate.
    if not prepared:
        return get_financial_assistant_response(
            question,
            config=llm_config,
            client=client,
        )

    grounded_question = build_grounded_question(
        question,
        prepared,
    )

    required_input_chars = (
        pipeline_config.max_context_chars
        + len(question)
        + 500
    )

    effective_config = (
        replace(
            llm_config,
            max_input_chars=required_input_chars,
        )
        if llm_config.max_input_chars < required_input_chars
        else llm_config
    )

    logger.info(
        "Grounded request prepared with %d context chunks.",
        len(prepared),
    )

    return get_financial_assistant_response(
        grounded_question,
        config=effective_config,
        client=client,
    )


def get_faq_grounded_response(
    user_question: str,
    top_k: int = 3,
) -> str:
    """Retrieve verified HisabDo FAQ content and answer from it."""

    if not isinstance(user_question, str) or not user_question.strip():
        return "Please enter a valid question."

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        return "Please provide a valid retrieval limit."

    try:
        from .faq_rag import get_retriever

        retriever = get_retriever()
        documents = retriever.retrieve(
            user_question.strip(),
            top_k=top_k,
        )

    except Exception:
        logger.exception("HisabDo FAQ retrieval failed.")
        return (
            "I couldn't search the HisabDo knowledge base right now. "
            "Please try again later."
        )

    if not documents:
        return (
            "I couldn't find relevant verified information in the "
            "HisabDo documentation or FAQs. Please contact HisabDo "
            "support for confirmation."
        )

    context_chunks = []

    for document in documents:
        if not isinstance(document, dict):
            continue

        title = document.get("title") or "HisabDo FAQ"
        content = document.get("text")

        if not isinstance(content, str) or not content.strip():
            continue

        source = document.get("source") or title

        context_chunks.append(
            {
                "text": content,
                "source": source,
                "score": document.get("score"),
            }
        )

    if not context_chunks:
        return (
            "I couldn't find usable information in the retrieved "
            "HisabDo documentation. Please contact support."
        )

    return get_grounded_financial_assistant_response(
        user_question=user_question.strip(),
        raw_context_chunks=context_chunks,
    )
