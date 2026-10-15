"""
dialogue - intent recognition and conversation state for the chat service.

    models.py        intents, routes, slots, conversation state, actions
    extract.py       amounts, currency, dates, periods, names, yes/no (English, Roman Urdu, Urdu)
    categories.py    team's expense categories (+ Roman Urdu/Urdu words); PROPOSED income categories
    recognizer.py    rule-based intent recognizer
    manager.py       the intent router + multi-turn slot filling + confirmation
    replies.py       fixed reply templates (English / Roman Urdu)
    account_data.py  private route: user's own numbers from the backend financial API only
    state_store.py   where the conversation state lives between messages
"""
from .account_data import AccountDataProvider, create_account_data_provider
from .manager import DialogueManager
from .models import ConversationState, DialogueOutcome, FlowStatus, Intent, Route, TransactionAction

__all__ = ["AccountDataProvider", "ConversationState", "DialogueManager", "DialogueOutcome", "FlowStatus",
           "Intent", "Route", "TransactionAction", "create_account_data_provider"]
