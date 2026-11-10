"""Conversation management: create, list, rename, archive, delete, and the
message history the chatbot replays to Claude.

Lifecycle::

    create ──► active ──archive──► archived
                 ▲  │ ◄─unarchive──   │
                 │  └────delete───────┴──► deleted ──purge_deleted()──► gone

* Messages can only be added while ``active``; ``archived`` is read-only
  (``ConversationArchived``) until unarchived. Rename works in both states.
* ``delete`` is a soft delete: ``deleted_at`` is set and the conversation
  disappears from every read, exactly as if it never existed. A retention job
  calls ``purge_deleted`` to hard-delete it and its messages later.
* A conversation is private to the user who created it. Every query filters on
  ``user_id`` *and* ``business_id``; someone else's conversation raises
  ``ConversationNotFound``, same as a missing one, so IDs can't be probed.
* IDs are random (``conv_<32 hex>``), never sequential, so they can't be guessed.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from .models import User
from .repository import Repository

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL REFERENCES businesses(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    title_source TEXT NOT NULL DEFAULT 'auto' CHECK (title_source IN ('auto', 'user')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_message_at TEXT,
    message_count INTEGER NOT NULL DEFAULT 0,
    focus_customer_ids TEXT NOT NULL DEFAULT '[]',
    deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_conversations_owner
    ON conversations(user_id, business_id, status, deleted_at);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_messages_conversation ON messages(conversation_id, id);
"""

DEFAULT_TITLE = "New conversation"
TITLE_MAX = 60


class ConversationNotFound(LookupError):
    pass


class ConversationArchived(RuntimeError):
    pass


@dataclass(frozen=True)
class Message:
    id: int
    conversation_id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Conversation:
    id: str
    business_id: str
    user_id: str
    title: str
    title_source: str  # "auto" (from first question) | "user" (set by create/rename)
    status: str  # "active" | "archived"
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None
    message_count: int
    focus_customer_ids: list[str]


def auto_title(text: str) -> str:
    """Title from the first question: first line, whitespace collapsed, cut at a word boundary."""
    stripped = text.strip()
    line = re.sub(r"\s+", " ", stripped.splitlines()[0]).strip() if stripped else ""
    if not line:
        return DEFAULT_TITLE
    if len(line) <= TITLE_MAX:
        return line
    cut = line[: TITLE_MAX - 1]
    if " " in cut[TITLE_MAX // 2 :]:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,.;:-") + "…"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)  # full precision: list order depends on it


class ConversationStore:
    def __init__(self, repo: Repository, clock: Callable[[], datetime] = _utcnow) -> None:
        self.repo = repo
        self.clock = clock
        with repo.connect() as conn:
            conn.executescript(SCHEMA)

    # --- lifecycle -----------------------------------------------------------------

    def create(self, user: User, title: str | None = None) -> Conversation:
        now = self.clock().isoformat()
        conv_id = f"conv_{uuid.uuid4().hex}"
        with self.repo.connect() as conn:
            conn.execute(
                "INSERT INTO conversations (id, business_id, user_id, title, title_source, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (conv_id, user.business_id, user.id, title or DEFAULT_TITLE, "user" if title else "auto", now, now),
            )
            return _to_conversation(self._fetch(conn, user, conv_id))

    def get(self, user: User, conv_id: str) -> Conversation:
        with self.repo.connect() as conn:
            return _to_conversation(self._fetch(conn, user, conv_id))

    def list(
        self, user: User, status: str = "active", limit: int = 20, offset: int = 0
    ) -> tuple[list[Conversation], int]:
        """Most recent activity first. Returns (page, total matching)."""
        where = "user_id = ? AND business_id = ? AND status = ? AND deleted_at IS NULL"
        args = (user.id, user.business_id, status)
        with self.repo.connect() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM conversations WHERE {where}", args).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM conversations WHERE {where}"
                " ORDER BY COALESCE(last_message_at, created_at) DESC, created_at DESC, id LIMIT ? OFFSET ?",
                (*args, limit, offset),
            ).fetchall()
        return [_to_conversation(r) for r in rows], total

    def rename(self, user: User, conv_id: str, title: str) -> Conversation:
        return self._update(user, conv_id, title=title, title_source="user")

    def set_status(self, user: User, conv_id: str, status: str) -> Conversation:
        if status not in ("active", "archived"):
            raise ValueError(f"invalid status {status!r}")
        return self._update(user, conv_id, status=status)

    def delete(self, user: User, conv_id: str) -> None:
        now = self.clock().isoformat()
        with self.repo.connect() as conn:
            self._fetch(conn, user, conv_id)
            conn.execute("UPDATE conversations SET deleted_at = ?, updated_at = ? WHERE id = ?", (now, now, conv_id))

    def purge_deleted(self, older_than: timedelta) -> int:
        """Hard-delete conversations soft-deleted before ``now - older_than``. Run from a scheduled job."""
        cutoff = (self.clock() - older_than).isoformat()
        with self.repo.connect() as conn:
            # Messages are removed with their conversation via ON DELETE CASCADE.
            cur = conn.execute("DELETE FROM conversations WHERE deleted_at IS NOT NULL AND deleted_at <= ?", (cutoff,))
            return cur.rowcount

    # --- messages --------------------------------------------------------------------

    def messages(self, user: User, conv_id: str) -> list[Message]:
        with self.repo.connect() as conn:
            self._fetch(conn, user, conv_id)
            rows = conn.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id", (conv_id,)).fetchall()
        return [_to_message(r) for r in rows]

    def recent_turns(self, user: User, conv_id: str, max_turns: int) -> list[tuple[str, str]]:
        """The last ``max_turns`` (question, answer) pairs, oldest first, for replay to the model."""
        with self.repo.connect() as conn:
            self._fetch(conn, user, conv_id)
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
                (conv_id, max_turns * 2),
            ).fetchall()
        rows = list(reversed(rows))
        if rows and rows[0]["role"] == "assistant":  # never start replay mid-pair
            rows = rows[1:]
        return [(rows[i]["content"], rows[i + 1]["content"]) for i in range(0, len(rows) - 1, 2)]

    def append_turn(
        self,
        user: User,
        conv_id: str,
        question: str,
        answer: str,
        answer_metadata: dict,
        focus_customer_ids: list[str],
    ) -> Conversation:
        """Store a completed question/answer pair atomically.

        Re-checks the lifecycle inside the write transaction, so a conversation
        that was archived or deleted while the model was answering doesn't get
        the late turn written into it.
        """
        now = self.clock().isoformat()
        with self.repo.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._fetch(conn, user, conv_id)
            if row["status"] != "active":
                raise ConversationArchived(conv_id)
            conn.executemany(
                "INSERT INTO messages (conversation_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                [
                    (conv_id, "user", question, "{}", now),
                    (conv_id, "assistant", answer, json.dumps(answer_metadata), now),
                ],
            )
            # Auto-title from the first question, unless the user already named it.
            retitle = row["title_source"] == "auto" and row["message_count"] == 0
            conn.execute(
                "UPDATE conversations SET message_count = message_count + 2, last_message_at = ?,"
                " updated_at = ?, focus_customer_ids = ?, title = ? WHERE id = ?",
                (now, now, json.dumps(focus_customer_ids), auto_title(question) if retitle else row["title"], conv_id),
            )
            return _to_conversation(self._fetch(conn, user, conv_id))

    # --- helpers ---------------------------------------------------------------------

    def _fetch(self, conn, user: User, conv_id: str):
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ? AND business_id = ? AND deleted_at IS NULL",
            (conv_id, user.id, user.business_id),
        ).fetchone()
        if row is None:
            raise ConversationNotFound(conv_id)
        return row

    def _update(self, user: User, conv_id: str, **values) -> Conversation:
        values["updated_at"] = self.clock().isoformat()
        with self.repo.connect() as conn:
            self._fetch(conn, user, conv_id)
            assignments = ", ".join(f"{k} = ?" for k in values)
            conn.execute(f"UPDATE conversations SET {assignments} WHERE id = ?", (*values.values(), conv_id))
            return _to_conversation(self._fetch(conn, user, conv_id))


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _to_conversation(row) -> Conversation:
    d = dict(row)
    return Conversation(
        id=d["id"],
        business_id=d["business_id"],
        user_id=d["user_id"],
        title=d["title"],
        title_source=d["title_source"],
        status=d["status"],
        created_at=_dt(d["created_at"]),
        updated_at=_dt(d["updated_at"]),
        last_message_at=_dt(d["last_message_at"]),
        message_count=d["message_count"],
        focus_customer_ids=json.loads(d["focus_customer_ids"]),
    )


def _to_message(row) -> Message:
    d = dict(row)
    return Message(
        id=d["id"],
        conversation_id=d["conversation_id"],
        role=d["role"],
        content=d["content"],
        created_at=_dt(d["created_at"]),
        metadata=json.loads(d["metadata"]),
    )
