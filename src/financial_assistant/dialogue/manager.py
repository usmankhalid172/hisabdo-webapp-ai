"""
manager.py - the intent router and multi-turn conversation handling.

For every message:
    1. load the conversation state (forget it if older than 30 minutes)
    2. recognise the intent (recognizer.py)
    3. if a flow is in progress: is this the answer to our question, a confirmation,
       a cancel, a side question, or a brand-new entry?
    4. decide the ROUTE:
         transaction  -> collect missing slots with ONE short question at a time,
                         then show a summary and ask for confirmation,
                         then return a confirmed action for the app to save
         account_data -> private numbers, only from the authenticated data API
         knowledge    -> product FAQ, answered from the verified knowledge base
         general      -> normal assistant answer (AI model)
    5. save the updated state with the conversation

Nothing here writes to the database. Confirmed entries are returned as actions.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime, timezone

from . import extract
from .account_data import (AccountDataError, AccountDataNotConnected, AccountDataProvider,
                           NotConnectedAccountData, PeriodNotAvailable, today_period)
from .categories import category_names, match_category
from .models import (ConversationState, DialogueOutcome, FlowStatus, Intent, IntentResult, Language,
                             Route, Slots, TransactionAction)
from .recognizer import IntentRecognizer, RuleBasedIntentRecognizer
from .replies import money, say, summary

DELETE = re.compile(r"\b(delete|hata do|hatao|hata den|remove|mita do|ختم|ہٹا)\b", re.I)
MAX_FOLLOW_UPS = 6
KNOWN_CURRENCIES = {"PKR", "USD", "AED", "SAR", "EUR", "GBP", "INR", "CAD", "AUD", "QAR", "OMR", "KWD", "BHD"}


def karachi_today() -> date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Karachi")).date()
    except Exception:  # noqa: BLE001 - tzdata missing: fall back to the server date
        return date.today()


class DialogueManager:
    def __init__(
        self,
        recognizer: IntentRecognizer | None = None,
        account_data: AccountDataProvider | None = None,
        default_currency: Callable[[str], str | None] | None = None,
        today: Callable[[], date] = karachi_today,
    ):
        self.recognizer = recognizer or RuleBasedIntentRecognizer()
        self.account_data = account_data or NotConnectedAccountData()
        self.default_currency = default_currency or (lambda user_id: None)
        self.today = today

    # ------------------------------------------------------------------ entry point
    def handle(self, user_id: str, message: str, state: ConversationState) -> DialogueOutcome:
        now = datetime.now(timezone.utc)
        if state.expired(now):
            state.clear_flow()
        result = self.recognizer.recognize(message, self.today())
        try:
            if state.active_intent is not None:
                return self._continue(user_id, message, result, state)
            return self._start(user_id, message, result, state)
        finally:
            state.updated_at = now

    # ------------------------------------------------------------------ new message, nothing in progress
    def _start(self, user_id: str, message: str, result: IntentResult, state: ConversationState,
               prefix: str = "") -> DialogueOutcome:
        state.language = result.language
        lang, intent = result.language, result.intent

        if intent in (Intent.ADD_EXPENSE, Intent.ADD_INCOME):
            state.clear_flow()
            state.active_intent = intent
            state.slots = result.slots
            unclear = any(s in result.signals for s in ("direction_unclear", "amount_only"))
            state.slots.direction = None if unclear else ("expense" if intent == Intent.ADD_EXPENSE else "income")
            if state.slots.currency is None:
                state.slots.currency = self.default_currency(user_id)
            return self._advance(user_id, state, result, prefix)

        if intent == Intent.CORRECT_TRANSACTION or (intent == Intent.CATEGORIZE and state.recent_actions):
            if not state.recent_actions:
                return self._out(result, Route.TRANSACTION, FlowStatus.NONE, say("no_entry_to_fix", lang))
            state.clear_flow()
            state.active_intent = Intent.CORRECT_TRANSACTION
            state.slots = self._changes(message, result, state)
            state.slots.target_action_id = state.recent_actions[-1].action_id
            if not (state.slots.amount or state.slots.category or state.slots.date or state.slots.delete):
                return self._ask(result, state, "changes", say("ask_change", lang))
            return self._ask_confirmation(result, state)

        if intent == Intent.CATEGORIZE:
            category = match_category(message, None)
            if category is None:            # "how do I categorize an expense?" is a product question
                return self._out(result, Route.KNOWLEDGE, FlowStatus.NONE)
            return self._out(result, Route.TRANSACTION, FlowStatus.NONE,
                             say("category_suggestion", lang, category=category))

        if intent in (Intent.REPORT, Intent.ACCOUNT_QUERY):
            state.clear_flow()
            state.active_intent = intent
            state.slots = result.slots
            return self._advance(user_id, state, result, prefix)

        if intent in (Intent.CONFIRM, Intent.DENY):
            return self._out(result, Route.TRANSACTION, FlowStatus.NONE, say("nothing_to_confirm", lang))

        route = Route.KNOWLEDGE if intent == Intent.FAQ else Route.GENERAL
        return self._out(result, route, FlowStatus.NONE)

    # ------------------------------------------------------------------ a flow is in progress
    def _continue(self, user_id: str, message: str, result: IntentResult, state: ConversationState) -> DialogueOutcome:
        lang = state.language
        state.turns_in_flow += 1
        if state.turns_in_flow > MAX_FOLLOW_UPS:
            state.clear_flow()
            return self._out(result, Route.TRANSACTION, FlowStatus.CANCELLED, say("too_many_turns", lang))

        # A brand-new entry with its own amount replaces the unfinished one.
        if self._is_new_entry(result, state):
            state.clear_flow()
            return self._start(user_id, message, result, state, prefix=say("replaced", result.language))

        if state.awaiting == "confirmation":
            if result.intent == Intent.CONFIRM:
                return self._finish(user_id, result, state)
            updates = self._changes(message, result, state, only_values=True)
            if updates.filled():
                self._apply(state.slots, updates)
                return self._ask_confirmation(result, state)
            if result.intent == Intent.DENY or extract.is_no(message):
                state.clear_flow()
                return self._out(result, Route.TRANSACTION, FlowStatus.CANCELLED, say("cancelled", lang))
            if self._is_side_question(result, message, waiting_for_slot=False):
                return self._side_route(user_id, message, result, state)
            return self._out(result, Route.TRANSACTION, FlowStatus.AWAITING_CONFIRMATION,
                             say("confirm_again", lang, question=self._confirmation_text(state)))

        # Waiting for one specific slot.
        if result.intent == Intent.DENY or (extract.is_no(message) and not self._answers(state, message, result)):
            state.clear_flow()
            return self._out(result, Route.TRANSACTION, FlowStatus.CANCELLED, say("cancelled", lang))

        if self._answers(state, message, result):
            return self._advance(user_id, state, result)

        if self._is_side_question(result, message, waiting_for_slot=True):
            return self._side_route(user_id, message, result, state)

        awaited = state.awaiting
        question = say("ask_amount_again", lang) if awaited == "amount" else self._question_for(awaited, state)
        return self._out(result, Route.TRANSACTION, FlowStatus.COLLECTING, question, missing=[awaited])

    @staticmethod
    def _is_side_question(result: IntentResult, message: str, waiting_for_slot: bool) -> bool:
        """
        A real question about something else. While we wait for a slot, a short statement is
        probably a (bad) answer, so only a clear question counts; while we wait for yes/no,
        any longer message that is not yes/no is treated as a side request.
        """
        if result.intent in (Intent.FAQ, Intent.REPORT, Intent.ACCOUNT_QUERY):
            return result.confidence >= 0.5
        if result.intent == Intent.GENERAL:
            asked = "?" in message or "؟" in message
            return asked if waiting_for_slot else (asked or len(message.split()) >= 3)
        return False

    def _is_new_entry(self, result: IntentResult, state: ConversationState) -> bool:
        if result.intent not in (Intent.ADD_EXPENSE, Intent.ADD_INCOME) or result.slots.amount is None:
            return False
        if result.confidence < 0.5 or state.awaiting in ("amount", "direction"):
            return False
        # Needs its own money verb, not just an answer like "600".
        return any(s.startswith(("add_expense:", "add_income:")) for s in result.signals)

    # ------------------------------------------------------------------ slot handling
    def _answers(self, state: ConversationState, message: str, result: IntentResult) -> bool:
        """Fill the awaited slot from the reply. True if it was filled."""
        awaited, slots, text = state.awaiting, state.slots, extract.normalise(message)
        filled = False
        if awaited == "amount":
            amount = result.slots.amount or extract.extract_amount(text)
            if amount is not None:
                slots.amount, filled = amount, True
        elif awaited == "direction":
            if result.intent == Intent.ADD_INCOME or re.search(r"\b(income|aamdani|amdani|mile|mila|received|aaye)\b", text, re.I):
                slots.direction, filled = "income", True
            elif result.intent == Intent.ADD_EXPENSE or re.search(r"\b(expense|kharcha|kharch|diye|diya|spent|paid)\b", text, re.I):
                slots.direction, filled = "expense", True
            if filled:
                state.active_intent = Intent.ADD_INCOME if slots.direction == "income" else Intent.ADD_EXPENSE
        elif awaited == "currency":
            code = text.strip().upper()
            currency = extract.extract_currency(text) or (code if code in KNOWN_CURRENCIES else None)
            if currency:
                slots.currency, filled = currency, True
        elif awaited == "category":
            category = match_category(text, slots.direction) or self._free_text_category(text, result)
            if category:
                slots.category, filled = category, True
        elif awaited == "period":
            period = extract.extract_period(text, self.today())
            if period:
                slots.period, filled = period, True
        elif awaited == "account":
            chosen = self._choose_account(text, state.account_options)
            if chosen:
                slots.account_id, filled = chosen, True
        elif awaited == "changes":
            changes = self._changes(message, result, state)
            if changes.amount or changes.category or changes.date or changes.delete:
                self._apply(slots, changes)
                slots.delete = changes.delete
                filled = True

        # Values given along with the answer ("600, petrol, kal wala") fill other empty slots too.
        if awaited in ("amount", "category", "direction", "currency") or (filled and awaited != "changes"):
            for name in ("amount", "currency", "date", "counterparty"):
                if getattr(slots, name) is None and getattr(result.slots, name) is not None:
                    setattr(slots, name, getattr(result.slots, name))
            if slots.category is None and state.active_intent in (Intent.ADD_EXPENSE, Intent.ADD_INCOME):
                slots.category = match_category(text, slots.direction)
        return filled

    @staticmethod
    def _free_text_category(text: str, result: IntentResult) -> str | None:
        """Accept the user's own category name if the reply is short and is not something else."""
        clean = re.sub(r"[^\w &\-؀-ۿ]", "", text).strip()
        if not clean or len(clean.split()) > 4 or extract.extract_amount(clean) is not None:
            return None
        if result.intent in (Intent.FAQ, Intent.REPORT, Intent.ACCOUNT_QUERY, Intent.DENY) or "?" in text:
            return None
        return clean.title() if clean.isascii() else clean

    @staticmethod
    def _choose_account(text: str, options: list[dict[str, str]]) -> str | None:
        t = text.strip().lower()
        if t.isdigit() and 1 <= int(t) <= len(options):
            return options[int(t) - 1]["id"]
        matches = [o["id"] for o in options if t and (t in o["name"].lower() or o["name"].lower() in t)]
        return matches[0] if len(matches) == 1 else None

    def _changes(self, message: str, result: IntentResult, state: ConversationState, only_values: bool = False) -> Slots:
        direction = state.slots.direction
        if state.active_intent == Intent.CORRECT_TRANSACTION or not direction:
            target = state.recent_actions[-1] if state.recent_actions else None
            direction = "income" if target and target.type == "create_income" else "expense"
        changes = Slots(amount=result.slots.amount, date=result.slots.date, currency=result.slots.currency,
                        category=match_category(message, direction))
        if changes.category is None:
            m = re.search(r"category\s+(?:to\s+|ko\s+)?['\"]?([A-Za-z][\w &\-]{1,30}?)['\"]?\s*(?:kar|karo|kardo|kar do|$|\.)",
                          extract.normalise(message), re.I)
            if m and m.group(1).lower() not in ("mein", "me", "main"):
                changes.category = m.group(1).strip().title()
        if not only_values and DELETE.search(message):
            changes.delete = True
        return changes

    @staticmethod
    def _apply(slots: Slots, changes: Slots) -> None:
        for name in ("amount", "currency", "category", "date"):
            value = getattr(changes, name)
            if value is not None:
                setattr(slots, name, value)

    # ------------------------------------------------------------------ moving a flow forward
    def _advance(self, user_id: str, state: ConversationState, result: IntentResult, prefix: str = "") -> DialogueOutcome:
        intent, slots, lang = state.active_intent, state.slots, state.language

        if intent in (Intent.ADD_EXPENSE, Intent.ADD_INCOME):
            for name in ("direction", "amount", "currency", "category"):
                if getattr(slots, name) is None:
                    return self._ask(result, state, name, prefix + self._question_for(name, state))
            if slots.date is None:
                slots.date = self.today()         # shown in the summary, so the user can change it
            return self._ask_confirmation(result, state, prefix)

        if intent == Intent.CORRECT_TRANSACTION:
            return self._ask_confirmation(result, state, prefix)

        if intent == Intent.REPORT and slots.period is None:
            return self._ask(result, state, "period", prefix + say("ask_period", lang))

        if intent in (Intent.REPORT, Intent.ACCOUNT_QUERY):
            return self._private_answer(user_id, result, state, prefix)

        state.clear_flow()
        return self._out(result, Route.GENERAL, FlowStatus.NONE)

    def _question_for(self, slot: str | None, state: ConversationState) -> str:
        lang = state.language
        if slot == "category":
            key = "ask_category_income" if state.slots.direction == "income" else "ask_category_expense"
            return say(key, lang, options=", ".join(category_names(state.slots.direction)[:5]))
        if slot == "account":
            return say("ask_account", lang, options=self._account_list(state))
        if slot == "changes":
            return say("ask_change", lang)
        return say(f"ask_{slot}", lang)

    @staticmethod
    def _account_list(state: ConversationState) -> str:
        return " ".join(f"{i}) {o['name']}" for i, o in enumerate(state.account_options, start=1))

    def _ask(self, result: IntentResult, state: ConversationState, slot: str, question: str) -> DialogueOutcome:
        state.awaiting = slot
        return self._out(result, Route.TRANSACTION if state.active_intent not in (Intent.REPORT, Intent.ACCOUNT_QUERY)
                         else Route.ACCOUNT_DATA, FlowStatus.COLLECTING, question, missing=[slot], state=state)

    def _confirmation_text(self, state: ConversationState) -> str:
        lang, slots = state.language, state.slots
        if state.active_intent == Intent.CORRECT_TRANSACTION:
            target = self._target(state)
            old = summary(Slots(**_payload_slots(target.payload)), lang) if target else "?"
            if slots.delete:
                return say("confirm_delete", lang, old=old)
            new = Slots(**{**_payload_slots(target.payload), **{k: v for k, v in slots.model_dump().items()
                                                                if k in ("amount", "currency", "category", "date") and v is not None}})
            return say("confirm_update", lang, old=old, summary=summary(new, lang))
        key = "confirm_income" if slots.direction == "income" else "confirm_expense"
        return say(key, lang, summary=summary(slots, lang))

    def _ask_confirmation(self, result: IntentResult, state: ConversationState, prefix: str = "") -> DialogueOutcome:
        state.awaiting = "confirmation"
        return self._out(result, Route.TRANSACTION, FlowStatus.AWAITING_CONFIRMATION,
                         prefix + self._confirmation_text(state), state=state)

    def _target(self, state: ConversationState) -> TransactionAction | None:
        return next((a for a in state.recent_actions if a.action_id == state.slots.target_action_id), None)

    # ------------------------------------------------------------------ finishing
    def _finish(self, user_id: str, result: IntentResult, state: ConversationState) -> DialogueOutcome:
        lang, slots, flow = state.language, state.slots, state.active_intent
        if state.active_intent == Intent.CORRECT_TRANSACTION:
            target = self._target(state)
            if target is None:
                state.clear_flow()
                return self._out(result, Route.TRANSACTION, FlowStatus.CANCELLED, say("no_entry_to_fix", lang))
            old = summary(Slots(**_payload_slots(target.payload)), lang)
            if slots.delete:
                action = TransactionAction(type="delete_transaction", payload={"target_action_id": target.action_id})
                state.recent_actions = [a for a in state.recent_actions if a.action_id != target.action_id]
                reply = say("done_delete", lang, old=old)
            else:
                changes = {k: v for k, v in slots.model_dump(mode="json").items()
                           if k in ("amount", "currency", "category", "date") and v is not None}
                action = TransactionAction(type="update_transaction",
                                           payload={"target_action_id": target.action_id, "changes": changes})
                target.payload.update(changes)        # later corrections see the new values
                reply = say("done_update", lang, summary=summary(Slots(**_payload_slots(target.payload)), lang))
            state.clear_flow()
            return self._out(result, Route.TRANSACTION, FlowStatus.COMPLETED, reply, action=action, intent=flow)

        kind = "create_income" if slots.direction == "income" else "create_expense"
        payload = {k: v for k, v in slots.model_dump(mode="json").items()
                   if k in ("amount", "currency", "category", "date", "counterparty", "note") and v is not None}
        action = TransactionAction(type=kind, payload=payload)
        state.remember(action)
        reply = say("done_create", lang, summary=summary(slots, lang))
        state.clear_flow()
        return self._out(result, Route.TRANSACTION, FlowStatus.COMPLETED, reply, action=action, intent=flow)

    # ------------------------------------------------------------------ private route
    def _private_answer(self, user_id: str, result: IntentResult, state: ConversationState, prefix: str = "") -> DialogueOutcome:
        lang, slots, flow = state.language, state.slots, state.active_intent
        try:
            if slots.account_id is None:
                accounts = self.account_data.list_accounts(user_id)
                if not accounts:
                    state.clear_flow()
                    return self._out(result, Route.ACCOUNT_DATA, FlowStatus.COMPLETED, prefix + say("no_accounts", lang),
                                     intent=flow)
                if len(accounts) > 1:
                    state.account_options = [{"id": a.id, "name": a.name} for a in accounts]
                    return self._ask(result, state, "account", prefix + self._question_for("account", state))
                slots.account_id = accounts[0].id
            if state.active_intent == Intent.REPORT:
                data = self.account_data.summary(user_id, slots.account_id, slots.period)
                top = say("report_top", lang, category=data.top_expense_category,
                          amount=money(data.top_expense_amount, data.currency)) if data.top_expense_category else ""
                count = say("report_count", lang, count=data.transaction_count) if data.transaction_count is not None else ""
                reply = say("report", lang, account=data.account.name, period=data.period.label,
                            demo=", demo data" if data.account.data_mode == "demo" else "",
                            income=money(data.total_income, data.currency), expense=money(data.total_expense, data.currency),
                            net=money(data.net, data.currency), count=count, top=top)
            else:
                data = self.account_data.summary(user_id, slots.account_id, today_period(self.today()))
                reply = say("balance", lang, account=data.account.name,
                            demo=" (demo data)" if data.account.data_mode == "demo" else "",
                            balance=money(data.closing_balance, data.currency), as_of=self.today().strftime("%d %b %Y"))
        except AccountDataNotConnected:
            reply = say("no_account_data", lang)
        except PeriodNotAvailable:
            reply = say("period_not_available", lang, period=slots.period.label if slots.period else "")
        except AccountDataError:
            reply = say("account_data_error", lang)
        state.clear_flow()
        return self._out(result, Route.ACCOUNT_DATA, FlowStatus.COMPLETED, prefix + reply, intent=flow)

    def _side_route(self, user_id: str, message: str, result: IntentResult, state: ConversationState) -> DialogueOutcome:
        """Answer a different question without losing the unfinished entry."""
        state.turns_in_flow -= 1
        reminder_q = self._confirmation_text(state) if state.awaiting == "confirmation" else self._question_for(state.awaiting, state)
        reminder = say("pending_reminder", state.language, question=reminder_q)
        if result.intent in (Intent.REPORT, Intent.ACCOUNT_QUERY):
            saved = state.model_copy(deep=True)
            tmp = ConversationState(language=result.language, recent_actions=state.recent_actions)
            outcome = self._start(user_id, message, result, tmp)
            if tmp.active_intent is None:                    # private answer finished in one step
                state.__dict__.update(saved.__dict__)
                outcome.reply = f"{outcome.reply}\n\n{reminder}"
                outcome.pending_reminder = reminder
                return outcome
            state.__dict__.update(tmp.__dict__)              # it needs follow-ups: the report replaces the entry
            outcome.reply = say("replaced", state.language) + (outcome.reply or "")
            return outcome
        route = Route.KNOWLEDGE if result.intent == Intent.FAQ else Route.GENERAL
        return self._out(result, route, FlowStatus.COLLECTING if state.awaiting != "confirmation"
                         else FlowStatus.AWAITING_CONFIRMATION, pending_reminder=reminder)

    @staticmethod
    def _out(result: IntentResult, route: Route, status: FlowStatus, reply: str | None = None,
             missing: list[str] | None = None, action: TransactionAction | None = None,
             pending_reminder: str | None = None, state: ConversationState | None = None,
             intent: Intent | None = None) -> DialogueOutcome:
        intent = intent or (state.active_intent if state is not None and state.active_intent else result.intent)
        return DialogueOutcome(intent=intent, route=route, status=status, reply=reply, missing_slots=missing or [],
                               action=action, pending_reminder=pending_reminder, signals=result.signals)


def _payload_slots(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k in ("amount", "currency", "category", "date", "counterparty")}
