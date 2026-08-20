"""Prompt templates for the AI Financial Assistant.

Builds a grounded system prompt and per-intent user prompts. When an LLM
provider is enabled, retrieved knowledge-base context and computed financial facts are
injected into the prompt so the model is told exactly what to answer from
(grounding reduces hallucination). Numeric calculations always come from
the backend and are passed as facts, never recomputed by the model.
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are HisabDo, a financial assistant embedded in a budgeting app. "
    "Answer short, plain, factual responses using ONLY the 'Financial facts' and "
    "'Knowledge base context' supplied in each user turn. Never invent "
    "transaction amounts, category totals, or dates that are not present in the "
    "provided context. If the supplied facts are insufficient to answer, say you "
    "cannot determine it from the available data and suggest asking again with more "
    "detail. Do not provide personalised financial advice or disclose private data."
)

HELP_TEXT = (
    "I can answer questions about your expenses. Try asking things like:\n"
    "- How much did I spend this month?\n"
    "- What was my total spending last month?\n"
    "- Which category did I spend the most on?\n"
    "- Give me a summary of my July spending.\n"
    "- How can I save money?"
)


def build_system_prompt() -> str:
    """Return the static system prompt."""
    return SYSTEM_PROMPT


def build_user_prompt(user_question: str, facts: str, context: str) -> str:
    """Build a grounded user-turn prompt.

    ``facts`` is the deterministic backend-computed financial data and ``context``
    is the retrieved knowledge-base grounding (or a no-context marker). The model
    is instructed to answer only from these.
    """
    return (
        "User question: " + user_question + "\n"
        "Financial facts: " + facts + "\n"
        "Knowledge base context: " + (context or "no knowledge-base context retrieved") + "\n"
        "Answer the user question using only the above financial facts and context."
    )