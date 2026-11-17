"""Request validation for the CRUD API.

``*In`` models validate a complete record and are used for create *and* for
update: a PATCH body (``*Patch``, every field optional) is merged onto the
stored record and the merged result is re-validated with the ``*In`` model,
so cross-field rules (e.g. ``amount_paid <= amount``) can't be bypassed by
patching one field at a time.

Fields set by the server (``id``, ``business_id``, a note's author and
timestamp) are not accepted from clients: ``extra="forbid"`` rejects them.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]
Money = Annotated[float, Field(ge=0, le=1_000_000_000, allow_inf_nan=False)]

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE = re.compile(r"^\+?[0-9 ()-]{7,20}$")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CustomerIn(_Strict):
    name: Name
    company: Text = ""
    email: Text = ""
    phone: Text = ""
    status: Literal["lead", "active", "churned"] = "lead"
    last_contact: date | None = None
    tags: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]] = Field(
        default_factory=list, max_length=20
    )

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        if v and not _EMAIL.match(v):
            raise ValueError("not a valid email address")
        return v.lower()

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        if v and not _PHONE.match(v):
            raise ValueError("phone may contain only digits, spaces, (), - and a leading +")
        return v


class TaskIn(_Strict):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    status: Literal["open", "in_progress", "done"] = "open"
    priority: Literal["low", "medium", "high"] = "medium"
    description: LongText = ""
    due_date: date | None = None
    assignee_id: str | None = None
    customer_id: str | None = None


class NoteIn(_Strict):
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    customer_id: str | None = None


class _BalanceIn(_Strict):
    amount: Annotated[float, Field(gt=0, le=1_000_000_000, allow_inf_nan=False)]
    amount_paid: Money = 0.0
    description: Text = ""
    issue_date: date | None = None
    due_date: date | None = None

    @field_validator("amount", "amount_paid")
    @classmethod
    def _two_decimals(cls, v: float) -> float:
        if round(v, 2) != v:
            raise ValueError("at most 2 decimal places")
        return v

    @model_validator(mode="after")
    def _consistent(self):
        if self.amount_paid > self.amount:
            raise ValueError("amount_paid cannot exceed amount")
        if self.issue_date and self.due_date and self.due_date < self.issue_date:
            raise ValueError("due_date cannot be before issue_date")
        return self


class ReceivableIn(_BalanceIn):
    customer_id: Annotated[str, StringConstraints(min_length=1)]
    invoice_number: Text = ""


class PayableIn(_BalanceIn):
    vendor_name: Name
    bill_number: Text = ""


def _patch_model(model: type[BaseModel]) -> type[BaseModel]:
    """Same fields as ``model``, all optional, no defaults applied."""
    annotations = {name: (f.annotation | None) for name, f in model.model_fields.items()}
    return type(
        f"{model.__name__.removesuffix('In')}Patch",
        (_Strict,),
        {"__annotations__": annotations, **{name: None for name in annotations}},
    )


CustomerPatch = _patch_model(CustomerIn)
TaskPatch = _patch_model(TaskIn)
NotePatch = _patch_model(NoteIn)
ReceivablePatch = _patch_model(ReceivableIn)
PayablePatch = _patch_model(PayableIn)


ChatMessage = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
ConversationTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class ChatIn(_Strict):
    """POST /api/chat - omit conversation_id to start a new conversation."""

    message: ChatMessage
    conversation_id: str | None = None


class MessageIn(_Strict):
    """POST /api/conversations/{id}/messages"""

    message: ChatMessage


class ConversationCreate(_Strict):
    title: ConversationTitle | None = None


class ConversationPatch(_Strict):
    """Rename and/or archive/unarchive. Omitted fields are left unchanged."""

    title: ConversationTitle | None = None
    status: Literal["active", "archived"] | None = None

    @model_validator(mode="after")
    def _not_null(self):
        # Explicit nulls would mean "clear the title" / "no status" - neither is valid.
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self
