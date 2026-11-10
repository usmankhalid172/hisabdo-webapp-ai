"""Grounded answers from the approved knowledge base: retrieval + evidence rules (docs/grounded-answer-rules.md)."""

from .answer import Citation, GroundedAnswer, GroundedAnswerer, detect_language, numbered_context
from .retrieval import KbRetriever, Passage

__all__ = ["Citation", "GroundedAnswer", "GroundedAnswerer", "KbRetriever", "Passage", "detect_language",
           "numbered_context"]
