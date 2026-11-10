"""SQLite data access. Every read and write is scoped to one business (tenant).

The only unscoped lookups are ``get_user`` (to resolve who is signed in) and
``get_business``. Every other method takes ``business_id`` and puts it in the
WHERE clause. A record belonging to another business looks exactly like a
record that doesn't exist (``RecordNotFound``), so its existence never leaks.

Money is stored as integer minor units (paisa/cents) and exposed as floats
rounded to 2 decimals.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, fields
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

from .models import Business, Customer, Note, Payable, Receivable, Task, User

SCHEMA = """
CREATE TABLE IF NOT EXISTS businesses (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, industry TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '', services TEXT NOT NULL DEFAULT '[]',
    hours TEXT NOT NULL DEFAULT '', policies TEXT NOT NULL DEFAULT '{}',
    currency TEXT NOT NULL DEFAULT 'PKR',
    is_demo INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL REFERENCES businesses(id),
    name TEXT NOT NULL, email TEXT NOT NULL, role TEXT NOT NULL, timezone TEXT NOT NULL DEFAULT 'UTC',
    auth_id TEXT
);
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL REFERENCES businesses(id),
    name TEXT NOT NULL, company TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'lead' CHECK (status IN ('lead', 'active', 'churned')),
    last_contact TEXT, tags TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL REFERENCES businesses(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'done')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    description TEXT NOT NULL DEFAULT '', due_date TEXT,
    assignee_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL REFERENCES businesses(id),
    author_id TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
    content TEXT NOT NULL, customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS receivables (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL REFERENCES businesses(id),
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    amount INTEGER NOT NULL CHECK (amount > 0),
    amount_paid INTEGER NOT NULL DEFAULT 0 CHECK (amount_paid >= 0 AND amount_paid <= amount),
    invoice_number TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
    issue_date TEXT, due_date TEXT
);
CREATE TABLE IF NOT EXISTS payables (
    id TEXT PRIMARY KEY, business_id TEXT NOT NULL REFERENCES businesses(id),
    vendor_name TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    amount_paid INTEGER NOT NULL DEFAULT 0 CHECK (amount_paid >= 0 AND amount_paid <= amount),
    bill_number TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
    issue_date TEXT, due_date TEXT
);
CREATE INDEX IF NOT EXISTS ix_users_biz ON users(business_id);
CREATE INDEX IF NOT EXISTS ix_customers_biz ON customers(business_id);
CREATE INDEX IF NOT EXISTS ix_tasks_biz ON tasks(business_id);
CREATE INDEX IF NOT EXISTS ix_notes_biz ON notes(business_id);
CREATE INDEX IF NOT EXISTS ix_receivables_biz ON receivables(business_id);
CREATE INDEX IF NOT EXISTS ix_payables_biz ON payables(business_id);
"""


class RecordNotFound(LookupError):
    pass


class InvalidReference(ValueError):
    """A foreign key points at a record that doesn't exist in this business."""

    def __init__(self, field_name: str, value: str) -> None:
        super().__init__(f"{field_name}: no record {value!r} in this business")
        self.field = field_name


class Conflict(RuntimeError):
    """The operation would break referential integrity (e.g. deleting an invoiced customer)."""


@dataclass(frozen=True)
class Entity:
    table: str
    prefix: str
    cls: type
    money: tuple[str, ...] = ()
    json_fields: tuple[str, ...] = ()
    dates: tuple[str, ...] = ()
    datetimes: tuple[str, ...] = ()
    refs: dict[str, str] = field(default_factory=dict)  # field -> referenced entity kind


ENTITIES: dict[str, Entity] = {
    "users": Entity("users", "U", User),
    "customers": Entity("customers", "C", Customer, json_fields=("tags",), dates=("last_contact",)),
    "tasks": Entity(
        "tasks", "T", Task, dates=("due_date",), refs={"assignee_id": "users", "customer_id": "customers"}
    ),
    "notes": Entity(
        "notes", "N", Note, datetimes=("created_at",), refs={"author_id": "users", "customer_id": "customers"}
    ),
    "receivables": Entity(
        "receivables", "R", Receivable, money=("amount", "amount_paid"),
        dates=("issue_date", "due_date"), refs={"customer_id": "customers"},
    ),
    "payables": Entity("payables", "P", Payable, money=("amount", "amount_paid"), dates=("issue_date", "due_date")),
}


class Repository:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate(conn)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        # One short-lived connection per operation keeps this safe under
        # FastAPI's threadpool without sharing a connection across threads.
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:  # commits on success, rolls back on exception
                yield conn
        finally:
            conn.close()

    # --- identity ---------------------------------------------------------------

    def get_user(self, user_id: str) -> User:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise RecordNotFound("user")
        return self._to_record(ENTITIES["users"], row)

    def get_user_by_auth_id(self, auth_id: str) -> User:
        """The app user linked to a login-provider ID (the "sub" of a verified token)."""
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE auth_id = ?", (auth_id,)).fetchone()
        if row is None:
            raise RecordNotFound("user")
        return self._to_record(ENTITIES["users"], row)

    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        """Add columns introduced after a database was first created. Safe to run every start."""
        def columns(table: str) -> set[str]:
            return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}

        if "is_demo" not in columns("businesses"):
            conn.execute("ALTER TABLE businesses ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0")
        if "auth_id" not in columns("users"):
            conn.execute("ALTER TABLE users ADD COLUMN auth_id TEXT")
        # One login maps to at most one app user.
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_auth_id ON users(auth_id) WHERE auth_id IS NOT NULL")

    def get_business(self, business_id: str) -> Business:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM businesses WHERE id = ?", (business_id,)).fetchone()
        if row is None:
            raise RecordNotFound("business")
        d = dict(row)
        return Business(**{**d, "services": json.loads(d["services"]), "policies": json.loads(d["policies"]),
                           "is_demo": bool(d["is_demo"])})

    # --- tenant-scoped CRUD ---------------------------------------------------------

    def list(self, kind: str, business_id: str) -> list[Any]:
        ent = ENTITIES[kind]
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM {ent.table} WHERE business_id = ? ORDER BY id", (business_id,)
            ).fetchall()
        return [self._to_record(ent, r) for r in rows]

    def get(self, kind: str, business_id: str, record_id: str) -> Any:
        ent = ENTITIES[kind]
        with self.connect() as conn:
            row = self._fetch(conn, ent, business_id, record_id)
        return self._to_record(ent, row)

    def create(self, kind: str, business_id: str, values: dict) -> Any:
        ent = ENTITIES[kind]
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")  # serialize ID allocation
            self._check_refs(conn, ent, business_id, values)
            record_id = self._next_id(conn, ent)
            row = self._to_row(ent, {**values, "id": record_id, "business_id": business_id})
            cols = ", ".join(row)
            conn.execute(f"INSERT INTO {ent.table} ({cols}) VALUES ({', '.join('?' * len(row))})", list(row.values()))
            return self._to_record(ent, self._fetch(conn, ent, business_id, record_id))

    def update(self, kind: str, business_id: str, record_id: str, values: dict) -> Any:
        ent = ENTITIES[kind]
        values = {k: v for k, v in values.items() if k not in ("id", "business_id")}
        with self.connect() as conn:
            self._fetch(conn, ent, business_id, record_id)  # 404 if missing or another tenant's
            self._check_refs(conn, ent, business_id, values)
            if values:
                row = self._to_row(ent, values)
                assignments = ", ".join(f"{c} = ?" for c in row)
                conn.execute(
                    f"UPDATE {ent.table} SET {assignments} WHERE id = ? AND business_id = ?",
                    [*row.values(), record_id, business_id],
                )
            return self._to_record(ent, self._fetch(conn, ent, business_id, record_id))

    def delete(self, kind: str, business_id: str, record_id: str) -> None:
        ent = ENTITIES[kind]
        with self.connect() as conn:
            self._fetch(conn, ent, business_id, record_id)
            try:
                conn.execute(f"DELETE FROM {ent.table} WHERE id = ? AND business_id = ?", (record_id, business_id))
            except sqlite3.IntegrityError as e:
                raise Conflict(f"{record_id} is still referenced by other records") from e

    # --- seeding ---------------------------------------------------------------------

    def load_seed(self, path: str | Path) -> None:
        """Insert seed records with their fixed IDs. Idempotent: skips if data exists."""
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        with self.connect() as conn:
            if conn.execute("SELECT 1 FROM businesses LIMIT 1").fetchone():
                return
            for b in raw["businesses"]:
                d = {**b, "services": json.dumps(b.get("services", [])), "policies": json.dumps(b.get("policies", {}))}
                conn.execute(f"INSERT INTO businesses ({', '.join(d)}) VALUES ({', '.join('?' * len(d))})", list(d.values()))
            for kind in ("users", "customers", "tasks", "notes", "receivables", "payables"):
                ent = ENTITIES[kind]
                for rec in raw.get(kind, []):
                    row = self._to_row(ent, self._parse(ent, rec))
                    conn.execute(
                        f"INSERT INTO {ent.table} ({', '.join(row)}) VALUES ({', '.join('?' * len(row))})",
                        list(row.values()),
                    )

    # --- helpers -----------------------------------------------------------------------

    def _fetch(self, conn: sqlite3.Connection, ent: Entity, business_id: str, record_id: str) -> sqlite3.Row:
        row = conn.execute(
            f"SELECT * FROM {ent.table} WHERE id = ? AND business_id = ?", (record_id, business_id)
        ).fetchone()
        if row is None:
            raise RecordNotFound(ent.table)
        return row

    def _check_refs(self, conn: sqlite3.Connection, ent: Entity, business_id: str, values: dict) -> None:
        for field_name, kind in ent.refs.items():
            ref = values.get(field_name)
            if ref is None:
                continue
            target = ENTITIES[kind].table
            hit = conn.execute(
                f"SELECT 1 FROM {target} WHERE id = ? AND business_id = ?", (ref, business_id)
            ).fetchone()
            if hit is None:
                raise InvalidReference(field_name, ref)

    def _next_id(self, conn: sqlite3.Connection, ent: Entity) -> str:
        # IDs are global (not per business) so a citation is never ambiguous.
        n = conn.execute(
            f"SELECT COALESCE(MAX(CAST(SUBSTR(id, 3) AS INTEGER)), 0) FROM {ent.table}"
        ).fetchone()[0]
        return f"{ent.prefix}-{n + 1:03d}"

    @staticmethod
    def _parse(ent: Entity, rec: dict) -> dict:
        out = dict(rec)
        for f in ent.dates:
            if out.get(f):
                out[f] = date.fromisoformat(out[f])
        for f in ent.datetimes:
            if out.get(f):
                out[f] = datetime.fromisoformat(out[f])
        return out

    @staticmethod
    def _to_row(ent: Entity, values: dict) -> dict:
        row = {}
        for k, v in values.items():
            if k in ent.money:
                v = int(round(float(v) * 100))
            elif k in ent.json_fields:
                v = json.dumps(v)
            elif isinstance(v, (date, datetime)):
                v = v.isoformat()
            row[k] = v
        return row

    @staticmethod
    def _to_record(ent: Entity, row: sqlite3.Row) -> Any:
        d = dict(row)
        for f in ent.money:
            d[f] = d[f] / 100
        for f in ent.json_fields:
            d[f] = json.loads(d[f])
        for f in ent.dates:
            d[f] = date.fromisoformat(d[f]) if d.get(f) else None
        for f in ent.datetimes:
            d[f] = datetime.fromisoformat(d[f])
        known = {f.name for f in fields(ent.cls)}
        return ent.cls(**{k: v for k, v in d.items() if k in known})


def record_dict(record: Any) -> dict:
    return asdict(record)
