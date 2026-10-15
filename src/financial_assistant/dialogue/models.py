"""
dialogue/models.py - intents, routes, slots and the conversation state.

Words used here:
  intent   = what the user wants to do (add an expense, see a report ...)
  slot     = one piece of information an intent needs (amount, category, date ...)
  route    = which part of the system answers:
               transaction   - our own step-by-step flow (asks for missing slots, then confirms)
               account_data  - the user's PRIVATE numbers, only from the authenticated data API
               knowledge     - general HisabDo FAQs, from the verified knowledge base
               general       - normal assistant conversation (AI model)
  state    = what is in progress in this conversation (saved between messages)
"""
import datetime as dt
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

STATE_TTL = timedelta(minutes=30)   # an unfinished flow is forgotten after 30 minutes of silence
MAX_RECENT_ACTIONS = 5              # remembered so "change the last entry" works


class Intent(str, Enum):
    ADD_EXPENSE = "add_expense"
    ADD_INCOME = "add_income"
    CATEGORIZE = "categorize"
    CORRECT_TRANSACTION = "correct_transaction"
    REPORT = "report"
    ACCOUNT_QUERY = "account_query"    # private: "what is my balance?"
    FAQ = "faq"                        # general product question
    CONFIRM = "confirm"
    DENY = "deny"                      # no / cancel
    GREETING = "greeting"
    GENERAL = "general"


class Route(str, Enum):
    TRANSACTION = "transaction"
    ACCOUNT_DATA = "account_data"
    KNOWLEDGE = "knowledge"
    GENERAL = "general"


PRIVATE_INTENTS = {Intent.REPORT, Intent.ACCOUNT_QUERY}
TRANSACTION_INTENTS = {Intent.ADD_EXPENSE, Intent.ADD_INCOME, Intent.CATEGORIZE, Intent.CORRECT_TRANSACTION}


class Language(str, Enum):
    ENGLISH = "en"
    ROMAN_URDU = "roman_ur"   # Urdu script questions are also answered in Roman Urdu (HisabDo prompt rule)


class Period(BaseModel):
    start: date
    end: date
    label: str                # "this month", "September 2026" ...


class Slots(BaseModel):
    """Everything we may collect. Which ones are REQUIRED depends on the intent (see flows.py)."""

    amount: Decimal | None = None
    currency: str | None = None
    category: str | None = None
    date: dt.date | None = None
    counterparty: str | None = None      # "Ali" in "Ali ko 500 diye"
    note: str | None = None
    direction: Literal["expense", "income"] | None = None   # when we can't tell yet
    period: Period | None = None         # reports
    report_type: Literal["expense", "income", "all"] | None = None
    account_id: str | None = None        # reports, when the user has several accounts
    target_action_id: str | None = None  # corrections: which earlier entry
    delete: bool = False                 # corrections: remove instead of change

    def filled(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump(mode="json").items() if v not in (None, False)}


class TransactionAction(BaseModel):
    """
    The result of a CONFIRMED transaction flow.

    The AI service does NOT write to the database (tables and write APIs are owned by the
    web/backend team). The web or mobile app receives this action and saves it through its
    own authenticated API. action_id lets a later correction point at this entry.
    """

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["create_expense", "create_income", "update_transaction", "delete_transaction"]
    status: Literal["confirmed"] = "confirmed"
    payload: dict[str, Any]
    requires_client_execution: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationState(BaseModel):
    """Saved with the conversation. Small on purpose: no message text, only structured slots."""

    active_intent: Intent | None = None
    slots: Slots = Field(default_factory=Slots)
    awaiting: str | None = None          # the slot we just asked for, or "confirmation"
    language: Language = Language.ROMAN_URDU
    turns_in_flow: int = 0               # safety: give up after too many follow-ups
    recent_actions: list[TransactionAction] = Field(default_factory=list)
    account_options: list[dict[str, str]] = Field(default_factory=list)  # [{"id","name"}] when asking "which account?"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def expired(self, now: datetime) -> bool:
        return self.active_intent is not None and now - self.updated_at > STATE_TTL

    def clear_flow(self) -> None:
        self.active_intent, self.slots, self.awaiting, self.turns_in_flow = None, Slots(), None, 0
        self.account_options = []

    def remember(self, action: TransactionAction) -> None:
        self.recent_actions = [*self.recent_actions, action][-MAX_RECENT_ACTIONS:]


class IntentResult(BaseModel):
    intent: Intent
    confidence: float                    # 0..1, rule-based score
    slots: Slots = Field(default_factory=Slots)
    language: Language = Language.ROMAN_URDU
    signals: list[str] = Field(default_factory=list)   # which cues fired (for logs/tests; no user text)


class FlowStatus(str, Enum):
    COLLECTING = "collecting"                # asked a follow-up question
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"                  # action confirmed / report shown
    CANCELLED = "cancelled"
    NONE = "none"                            # nothing in progress


class DialogueOutcome(BaseModel):
    """What the dialogue manager decided for one message."""

    intent: Intent
    route: Route
    status: FlowStatus
    reply: str | None = None             # set for transaction/account_data routes (no AI model needed)
    missing_slots: list[str] = Field(default_factory=list)
    action: TransactionAction | None = None
    pending_reminder: str | None = None  # an unfinished flow is still waiting (for knowledge/general routes)
    signals: list[str] = Field(default_factory=list)
