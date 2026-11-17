"""Domain records the chatbot can ground its answers in.

Every record carries a stable, human-readable ``id`` (e.g. ``C-001``). Those IDs
are what the model cites, and what the grounding validator checks citations
against, so they are unique across all record types and all businesses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class User:
    id: str
    business_id: str
    name: str
    email: str
    role: str
    timezone: str = "UTC"
    auth_id: str | None = None  # the login provider's user ID (Supabase "sub")


@dataclass(frozen=True)
class Business:
    id: str
    name: str
    industry: str = ""
    description: str = ""
    services: list[str] = field(default_factory=list)
    hours: str = ""
    policies: dict[str, str] = field(default_factory=dict)
    currency: str = "PKR"
    is_demo: bool = False  # sample data: never presented as a real customer's figures


@dataclass(frozen=True)
class Customer:
    id: str
    business_id: str
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    status: str = "lead"  # lead | active | churned
    last_contact: date | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Task:
    id: str
    business_id: str
    title: str
    status: str = "open"  # open | in_progress | done
    priority: str = "medium"  # low | medium | high
    description: str = ""
    due_date: date | None = None
    assignee_id: str | None = None
    customer_id: str | None = None

    def is_open(self) -> bool:
        return self.status != "done"

    def is_overdue(self, today: date) -> bool:
        return self.is_open() and self.due_date is not None and self.due_date < today


@dataclass(frozen=True)
class Note:
    id: str
    business_id: str
    author_id: str
    created_at: datetime
    content: str
    customer_id: str | None = None


class _Balance:
    """Shared money logic for invoices we issued and bills we received."""

    amount: float
    amount_paid: float
    due_date: date | None

    @property
    def outstanding(self) -> float:
        return round(self.amount - self.amount_paid, 2)

    def state(self, today: date) -> str:
        if self.outstanding <= 0:
            return "paid"
        if self.due_date is not None and self.due_date < today:
            return "overdue"
        return "partially_paid" if self.amount_paid > 0 else "unpaid"


@dataclass(frozen=True)
class Receivable(_Balance):
    """An invoice a customer owes the business."""

    id: str
    business_id: str
    customer_id: str
    amount: float
    amount_paid: float = 0.0
    invoice_number: str = ""
    description: str = ""
    issue_date: date | None = None
    due_date: date | None = None


@dataclass(frozen=True)
class Payable(_Balance):
    """A bill the business owes a supplier/vendor."""

    id: str
    business_id: str
    vendor_name: str
    amount: float
    amount_paid: float = 0.0
    bill_number: str = ""
    description: str = ""
    issue_date: date | None = None
    due_date: date | None = None
