"""Grounded response builders for the AI Financial Assistant.

Each supported intent has a deterministic responder that turns backend-computed
facts into a short, plain-language answer. The builders only use data provided
to them; they never invent figures (hallucination guard). Ambiguous and
unsupported intents get safe fallback responses.
"""

from __future__ import annotations

from typing import List

from .retriever import RetrievedChunk


def _fmt_month(period: str) -> str:
    try:
        parts = period.split("-")
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November",
                       "December"]
        return f"{month_names[int(parts[1]) - 1]} {parts[0]}"
    except (IndexError, ValueError):
        return period


def _money(value) -> str:
    return f"PKR {value:,.2f}" if isinstance(value, (int, float)) else str(value)


def respond_monthly_expense(facts: dict) -> str:
    period = facts.get("period", "")
    total = facts.get("total", 0.0)
    count = facts.get("count", 0)
    return (
        f"Your total spending for {_fmt_month(period)} was {_money(total)} "
        f"across {count} transactions."
    )


def respond_category_expense(facts: dict) -> str:
    """Respond for a category-scoped monthly query (e.g. spending on groceries)."""
    period = facts.get("period", "")
    category = facts.get("category", "")
    total = facts.get("total", 0.0)
    return (
        f"Your spending on {category} in {_fmt_month(period)} was "
        f"{_money(total)}."
    )


def respond_highest_category(facts: dict) -> str:
    if not facts.get("category"):
        # No category is only expected when no transactions matched the period.
        if facts.get("period"):
            return (
                f"I could not find any transactions for "
                f"{_fmt_month(facts['period'])}, so I cannot determine the "
                "highest spending category. Please try another month."
            )
        return (
            "I could not find any transactions for that period, so I cannot "
            "determine the highest spending category. Please try another month."
        )
    category = facts.get("category")
    amount = facts.get("amount", 0.0)
    period = facts.get("period")
    scope = f"in {_fmt_month(period)}" if period else "over the available data"
    return (
        f"Your highest spending category {scope} was {category} "
        f"at {_money(amount)}."
    )


def respond_spending_summary(facts: dict) -> str:
    period = facts.get("period", "the selected period")
    if "categories" not in facts or not facts["categories"]:
        return (
            f"I could not find any transactions for {_fmt_month(period)}, so I "
            "cannot build a spending summary."
        )
    total = facts.get("total", 0.0)
    lines = [
        f"Here is your spending summary for {_fmt_month(period)} "
        f"(total {_money(total)}):"
    ]
    for category, amount in facts["categories"].items():
        lines.append(f"- {category}: {_money(amount)}")
    return "\n".join(lines)


def respond_saving_tip(retrieved: List[RetrievedChunk], query: str) -> str:
    if not retrieved:
        return (
            "I could not find saving tips related to that question in my "
            "knowledge base. Try asking something like 'Give me saving tips' "
            "or 'How can I reduce my spending?'"
        )
    tips = ["Here are some saving tips I found in my knowledge base:"]
    for rc in retrieved:
        tips.append(f"- {rc.chunk.title.replace(' to save', '').capitalize()}: {rc.chunk.text}")
    tips.append(
        "Note: these are general suggestions from the HisabDo knowledge base, "
        "not personalised financial advice."
    )
    return "\n".join(tips)


# Intent-specific safe handling.
def respond_ambiguous() -> str:
    return (
        "Could you tell me which time period you mean? For example: "
        "'How much did I spend this month?', 'What did I spend in July?', "
        "or 'Give me a summary of last month'."
    )


def respond_unsupported() -> str:
    return (
        "I am a financial assistant and can only help with questions about your "
        "expenses, spending summaries, and saving tips. Ask me for help if you "
        "would like examples of what I can do."
    )


def respond_help() -> str:
    from .prompts import HELP_TEXT
    return HELP_TEXT


def respond_greeting() -> str:
    return (
        "Hello! I am your HisabDo financial assistant. Ask me about your "
        "monthly spending, your highest spending category, a spending summary, "
        "or saving tips."
    )


def respond_thanks() -> str:
    return "You are welcome! Feel free to ask about your expenses or saving tips anytime."