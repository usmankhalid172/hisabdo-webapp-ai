"""
state_store.py - where a conversation's dialogue state lives between messages.

The backend calls this service once per message (POST /api/v1/chatbot) and
sends the chat history itself, but the history is plain text. Multi-turn slot
filling needs structured state (which intent is in progress, which slots are
filled, what we are waiting for), so it is kept here, keyed by
(user_id, conversation_id) - the same user can never load another user's state.

InMemoryStateStore: fine for one server process (local dev, the current single
Render instance). With several instances, or across restarts, the state must
move to shared storage (Redis / the backend DB) - same two methods, decision
for the team lead / backend team. Unfinished flows expire after 30 minutes
anyway (models.STATE_TTL), and finished flows keep only the last 5 entry IDs.
"""
from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections import OrderedDict
from functools import lru_cache

from .models import ConversationState

MAX_CONVERSATIONS = 10_000   # memory guard: oldest conversations are dropped first


class DialogueStateStore(ABC):
    @abstractmethod
    def load(self, user_id: str, conversation_id: str) -> ConversationState: ...

    @abstractmethod
    def save(self, user_id: str, conversation_id: str, state: ConversationState) -> None: ...


class InMemoryStateStore(DialogueStateStore):
    def __init__(self, max_conversations: int = MAX_CONVERSATIONS):
        self._data: OrderedDict[tuple[str, str], ConversationState] = OrderedDict()
        self._lock = threading.Lock()
        self._max = max_conversations

    def load(self, user_id: str, conversation_id: str) -> ConversationState:
        with self._lock:
            state = self._data.get((user_id, conversation_id))
            return state.model_copy(deep=True) if state else ConversationState()

    def save(self, user_id: str, conversation_id: str, state: ConversationState) -> None:
        with self._lock:
            key = (user_id, conversation_id)
            self._data[key] = state.model_copy(deep=True)
            self._data.move_to_end(key)
            while len(self._data) > self._max:
                self._data.popitem(last=False)


@lru_cache
def get_state_store() -> DialogueStateStore:
    return InMemoryStateStore()
