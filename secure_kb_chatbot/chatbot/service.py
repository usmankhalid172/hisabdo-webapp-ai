"""Orchestrates one chat turn:

    resolve conversation -> fetch business data -> build context
    -> inject into system prompt -> call Claude -> validate grounding
    -> persist the turn

Conversations and their messages live in the database (see conversations.py),
so history survives restarts. Only the plain question/answer text of
completed turns is stored and replayed; the business context is rebuilt from
the database each turn. A failed or refused turn is returned to the caller but
not stored. The last MAX_TURNS exchanges are replayed to the model.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import date

from .context_builder import ContextBuilder
from .conversations import Conversation, ConversationArchived, ConversationStore
from .grounding import GroundedAnswer, validate
from .llm import LLMClient
from .models import User
from .periods import local_today
from .prompts import build_system
from .retrieval import KBRetriever, NoteIndex, RetrievalResult

MAX_TURNS = 12


@dataclass
class ChatReply:
    conversation: Conversation
    result: GroundedAnswer
    context_sources: dict[str, list[str]]
    context_totals: dict[str, int]
    kb: RetrievalResult | None = None
    sources: list[dict] = field(default_factory=list)  # KB entries the answer actually cited


class ChatService:
    def __init__(
        self,
        builder: ContextBuilder,
        llm: LLMClient,
        conversations: ConversationStore,
        today: date | None = None,
        retriever: KBRetriever | None = None,
        note_index: NoteIndex | None = None,
        timezone: str = "Asia/Karachi",
    ) -> None:
        self.builder = builder
        self.llm = llm
        self.conversations = conversations
        self._today = today
        self.retriever = retriever
        self.note_index = note_index
        self.timezone = timezone
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def today(self) -> date:
        # The business's local date, not the server's: decides what is "overdue" and "today".
        return self._today or local_today(self.timezone)

    def ask(self, user: User, question: str, conversation_id: str | None = None) -> ChatReply:
        """Answer ``question``, starting a new conversation when no ID is given.

        Raises ConversationNotFound for an unknown, deleted, or someone else's
        conversation, and ConversationArchived for an archived one.
        """
        conv = (
            self.conversations.create(user)
            if conversation_id is None
            else self.conversations.get(user, conversation_id)
        )
        if conv.status != "active":
            raise ConversationArchived(conv.id)  # fail fast, before paying for a model call

        # One turn at a time per conversation, so history stays in order.
        with self._lock_for(conv.id):
            turns = self.conversations.recent_turns(user, conv.id, MAX_TURNS)
            # Semantic retrieval. With no retriever configured the status is "unavailable",
            # which the prompt turns into "product information is temporarily unavailable"
            # - never into an answer from the model's general knowledge.
            kb = self.retriever.retrieve(question) if self.retriever else RetrievalResult("unavailable")
            ranker = None
            if self.note_index is not None:
                ranker = lambda notes: self.note_index.rank(user.business_id, notes, kb.query_vector)  # noqa: E731
            bundle = self.builder.build(
                user.id, question, self.today(), conv.focus_customer_ids, kb=kb, note_ranker=ranker
            )
            messages: list[dict] = []
            for q, a in turns:
                messages += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
            messages.append({"role": "user", "content": question})

            result = self.llm.generate(build_system(bundle.text), messages)

            if result.stop_reason == "refusal":
                answer = GroundedAnswer(
                    answer="I can't help with that request.",
                    citations=[],
                    grounding="refused",
                    warnings=[f"Declined by safety policy (category: {result.refusal_category or 'unspecified'})."],
                )
            elif result.data is None:
                answer = GroundedAnswer(
                    answer="Sorry, I couldn't produce a complete answer. Please try again or narrow the question.",
                    citations=[],
                    grounding="error",
                    warnings=[f"Model stopped with stop_reason={result.stop_reason!r} and no valid output."],
                )
            else:
                answer = validate(result.data, bundle.source_ids, bundle.text)
                cited_customers = [c for c in answer.citations if c in bundle.included["customers"]]
                focus = bundle.focus_customer_ids or cited_customers or conv.focus_customer_ids
                conv = self.conversations.append_turn(
                    user,
                    conv.id,
                    question,
                    answer.answer,
                    {
                        "citations": answer.citations,
                        "grounding": answer.grounding,
                        "missing_information": answer.missing_information,
                        "warnings": answer.warnings,
                    },
                    focus,
                )

            return ChatReply(
                conversation=conv,
                result=answer,
                context_sources=bundle.included,
                context_totals=bundle.totals,
                kb=kb,
                sources=[
                    {"id": s.id, "title": s.title, "source": s.source, "kb_version": s.kb_version, "relevance": s.score}
                    for s in kb.sources if s.id in answer.citations
                ],
            )

    def _lock_for(self, conversation_id: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(conversation_id, threading.Lock())
