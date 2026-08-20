"""Transaction data loading and backend financial computation.

Per the team's RAG/ML research (Farheen's note), financial calculations are
performed in the backend / deterministic code rather than delegated to an LLM.
This module loads the synthetic sample transactions and computes monthly
totals, highest categories and summaries.

The core module deliberately uses only the standard library (``csv``,
``datetime``) so the assistant flow is portable and offline-friendly.
"""

from __future__ import annotations

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path
from typing import Optional, Sequence

DataDirectory = Path(__file__).resolve().parent.parent.parent / "data"


class Transaction:
    """A single expense transaction."""

    def __init__(self, date: str, category: str, description: str, amount: float):
        self.date = date
        self.category = category
        self.description = description
        self.amount = round(float(amount), 2)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "category": self.category,
            "description": self.description,
            "amount": self.amount,
        }


def load_transactions(path=None) -> list:
    """Load transactions from a CSV with columns date,category,description,amount."""
    path = path or (DataDirectory / "sample_transactions.csv")
    transactions = []
    with open(str(path), newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            transactions.append(
                Transaction(row["date"], row["category"],
                            row["description"], float(row["amount"]))
            )
    return transactions


def _period_prefix(period: str) -> str:
    """Return the ``YYYY-MM`` prefix for a month period string."""
    return period[:7]


def _in_period(txn: Transaction, period: str) -> bool:
    """True if the transaction date falls in the ``YYYY-MM`` period."""
    return txn.date.startswith(_period_prefix(period))


def total_for_period(transactions: list, period: str) -> float:
    """Total spending for a ``YYYY-MM`` period."""
    return round(
        sum(t.amount for t in transactions if _in_period(t, period)), 2
    )


def highest_category_for_period(transactions: list, period=None) -> dict:
    """Return the category with the highest total spend.

    If ``period`` is provided, only transactions in that ``YYYY-MM`` period are
    considered. Returns a ``{category, amount, count}`` dict or ``None``.
    """
    totals = defaultdict(float)
    counts = defaultdict(int)
    for t in transactions:
        if period and not _in_period(t, period):
            continue
        totals[t.category] += t.amount
        counts[t.category] += 1
    if not totals:
        return None
    top_category = max(totals, key=totals.get)
    return {
        "category": top_category,
        "amount": round(totals[top_category], 2),
        "count": counts[top_category],
    }


def category_totals(transactions: list, period=None) -> dict:
    """Return ``{category: amount}`` totals, optionally filtered by period."""
    grouped = defaultdict(float)
    for t in transactions:
        if period and not _in_period(t, period):
            continue
        grouped[t.category] += t.amount
    ordered = dict(sorted(grouped.items(), key=lambda kv: kv[1], reverse=True))
    return {k: round(v, 2) for k, v in ordered.items()}


def summary_for_period(transactions: list, period: str) -> dict:
    """Build a spending summary dict for a ``YYYY-MM`` period."""
    scoped = [t for t in transactions if _in_period(t, period)]
    total = round(sum(t.amount for t in scoped), 2)
    categories = category_totals(scoped)
    count = len(scoped)
    return {
        "period": period,
        "total": total,
        "count": count,
        "categories": categories,
    }


def monthly_series(transactions: list) -> dict:
    """Group totals per month ``YYYY-MM`` -> total."""
    grouped = defaultdict(float)
    for t in transactions:
        grouped[t.date[:7]] += t.amount
    return {k: round(v, 2) for k, v in sorted(grouped.items())}