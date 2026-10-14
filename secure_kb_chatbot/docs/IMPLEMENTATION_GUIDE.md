# Implementation Guide: Secure Financial Data and a Semantic Knowledge Base

This guide adds two things to your chatbot in `HisabDO/conversation-management`:

- **Part A, security (Day 4 task):** real authentication, protection against one customer reading another's data, demo-vs-actual labelling, and accurate reporting periods.
- **Part B, knowledge base (Day 5 task):** semantic search with embeddings in place of keyword matching, a relevance threshold, source attribution, a safe fallback, and a versioned knowledge base of verified content.

## Read this first

**What has been tested.** Every piece of code in this guide was built and run against a copy of your project. With all steps applied, **258 tests pass**: your existing 161 plus 97 new ones. I also broke 11 security and retrieval controls on purpose, one at a time, and the new tests caught all 11.

**What has not been tested.** Two things need real credentials, which I don't have:

- **Gemini embeddings.** The calls match the installed `google-genai` library, but no real embedding has been created. Step 14 is where you do that.
- **Real Supabase logins.** Token checking is tested with tokens I generated myself, not ones issued by your team's Supabase project.

**Two ways to use this guide:**

- **To learn (recommended):** follow the steps in order and type or paste each change yourself. Each step says why it exists and how to check it.
- **To finish fast:** copy the `reference/` folder over your project. It contains the final version of every new and changed file.

```powershell
Copy-Item -Recurse -Force C:\Users\Comtech\HisabDO\implementation-guide\reference\* C:\Users\Comtech\HisabDO\conversation-management\
```

**Before you start:**

1. Work on a copy or a Git branch, so you can go back.
2. Install the two new libraries:

```powershell
pip install pyjwt tzdata
```

3. Confirm your starting point. From `conversation-management`, this should print `161 passed`:

```powershell
pytest -q
```

## Which step covers which task

| Task | Steps |
|---|---|
| Authentication and authorization checks | 1, 3, 12 |
| Prevent cross-customer access; secure account-specific financial data | 3, 12 |
| Demo vs actual data; account association | 2, 12 |
| Reporting-period accuracy | 4, 11, 12 |
| Security test cases | 13 |
| Replace token matching with semantic search / embeddings | 6, 7, 8, 10 |
| Relevance threshold | 8, 14 |
| Source attribution | 9, 10, 11, 12 |
| Safe fallback | 8, 9, 11 |
| Expand and version the knowledge base with verified content | 5, 14 |

**Checkpoints where the tests must pass:** after Step 2 (161), after Step 11 (161), after Step 12 (161) and after Step 13 (258). Between other steps the project still runs, but there is nothing new to test yet.

---

# Part A: Security

## Step 1: Central settings (`chatbot/config.py`, new file)

**Why.** Today the app trusts an `X-User-Id` header: anyone who types `U-001` becomes that user. Before fixing that, the app needs one place that decides how it is allowed to run. Three rules are built in:

- **Secure by default.** With nothing configured, authentication is "disabled", which means every request is rejected, not that every request is allowed.
- **Dev mode needs two switches.** The no-password mode only works when `ALLOW_DEV_AUTH=true` is set and `APP_ENV` is not `production`. One wrong variable on a server can't turn login off. This was the main finding (AUTH-P9) in the Day 4 report on your teammate's API.
- **Fail at startup.** `validate()` refuses to start with an unsafe setup, such as a signing secret shorter than 32 characters.

**Do this.** Create `chatbot/config.py`:

```python
"""Settings, read once from environment variables (.env is never committed).

Secure by default: with nothing configured, authentication is off (every
request gets 401), demo data is hidden, and the knowledge base is unused.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

MIN_JWT_SECRET_LENGTH = 32


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # --- authentication -------------------------------------------------------------
    # "supabase": Authorization: Bearer <Supabase access token>   (production)
    # "dev":      X-User-Id header, no password                    (your laptop only)
    # anything else: every request is rejected with 401
    auth_mode: str = "disabled"
    # Dev mode needs BOTH this flag and a non-production APP_ENV, so one wrong
    # variable on a server can't switch authentication off.
    allow_dev_auth: bool = False
    app_env: str = "production"
    supabase_jwt_secret: str = field(default="", repr=False)  # never printed or logged
    supabase_jwt_audience: str = "authenticated"

    # --- data ---------------------------------------------------------------------------
    allow_demo_data: bool = False  # businesses flagged is_demo are blocked unless this is on
    reporting_timezone: str = "Asia/Karachi"  # "today" and report periods use this, not the server clock
    max_period_days: int = 366

    # --- knowledge base retrieval -----------------------------------------------------
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768
    kb_threshold: float = 0.60  # minimum cosine similarity; calibrate with scripts/calibrate_threshold.py
    kb_top_k: int = 4
    note_threshold: float = 0.55

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            auth_mode=os.getenv("AUTH_MODE", "disabled").strip().lower(),
            allow_dev_auth=_flag("ALLOW_DEV_AUTH"),
            app_env=os.getenv("APP_ENV", "production").strip().lower(),
            supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", "").strip(),
            supabase_jwt_audience=os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip(),
            allow_demo_data=_flag("ALLOW_DEMO_DATA"),
            reporting_timezone=os.getenv("REPORTING_TIMEZONE", "Asia/Karachi").strip(),
            max_period_days=int(os.getenv("MAX_PERIOD_DAYS", "366")),
            embedding_model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip(),
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "768")),
            kb_threshold=float(os.getenv("KB_THRESHOLD", "0.60")),
            kb_top_k=int(os.getenv("KB_TOP_K", "4")),
            note_threshold=float(os.getenv("NOTE_THRESHOLD", "0.55")),
        )

    def validate(self) -> None:
        """Fail at startup, not at the first request, when the configuration is unsafe."""
        if self.auth_mode == "dev" and (self.is_production or not self.allow_dev_auth):
            raise RuntimeError(
                "AUTH_MODE=dev is refused: it needs ALLOW_DEV_AUTH=true and APP_ENV other than 'production'."
            )
        if self.auth_mode == "supabase" and len(self.supabase_jwt_secret) < MIN_JWT_SECRET_LENGTH:
            raise RuntimeError(
                f"SUPABASE_JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters (use the project's JWT secret)."
            )
```

## Step 2: Two new fields in the data model

**Why.**

- **`auth_id` on users** links a login (the user ID inside a Supabase token) to a user in your database. This is the "account association": the token says who you are, and this column says which business you belong to.
- **`is_demo` on businesses** marks sample data. Your seed data is made up, so it must never be presented as a real customer's books. The Day 4 report found exactly this problem (DEMO-P4) in your teammate's API: synthetic accounts labelled "actual".

**Do this (1 of 3).** Edit `chatbot/models.py`:

**Edit 1 of 2.** Find this text (it can be part of a line):

```python
    timezone: str = "UTC"
```

Replace it with:

```python
    timezone: str = "UTC"
    auth_id: str | None = None  # the login provider's user ID (Supabase "sub")
```

**Edit 2 of 2.** Find this text (it can be part of a line):

```python
    currency: str = "PKR"
```

Replace it with:

```python
    currency: str = "PKR"
    is_demo: bool = False  # sample data: never presented as a real customer's figures
```

**Do this (2 of 3).** Edit `chatbot/repository.py`. The `_migrate` function adds the new columns to a database that already exists, so nobody loses data when they update:

**Edit 1 of 5.** Find this text (it can be part of a line):

```python
    currency TEXT NOT NULL DEFAULT 'PKR'
```

Replace it with:

```python
    currency TEXT NOT NULL DEFAULT 'PKR',
    is_demo INTEGER NOT NULL DEFAULT 0
```

**Edit 2 of 5.** Find this text (it can be part of a line):

```python
role TEXT NOT NULL, timezone TEXT NOT NULL DEFAULT 'UTC'
```

Replace it with:

```python
role TEXT NOT NULL, timezone TEXT NOT NULL DEFAULT 'UTC',
    auth_id TEXT
```

**Edit 3 of 5.** Find this text (it can be part of a line):

```python
            conn.executescript(SCHEMA)
```

Replace it with:

```python
            conn.executescript(SCHEMA)
            self._migrate(conn)
```

**Edit 4 of 5.** Find this text (it can be part of a line):

```python
    def get_business(self, business_id: str) -> Business:
```

Replace it with:

```python
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
```

**Edit 5 of 5.** Find this text (it can be part of a line):

```python
        return Business(**{**d, "services": json.loads(d["services"]), "policies": json.loads(d["policies"])})
```

Replace it with:

```python
        return Business(**{**d, "services": json.loads(d["services"]), "policies": json.loads(d["policies"]),
                           "is_demo": bool(d["is_demo"])})
```

**Do this (3 of 3).** Update the seed data. Every business gets `"is_demo": true` and every user gets an `auth_id`. Copy the prepared file:

```powershell
Copy-Item -Force C:\Users\Comtech\HisabDO\implementation-guide\reference\data\seed.json C:\Users\Comtech\HisabDO\conversation-management\data\seed.json
```

Then delete your local database so it is rebuilt from the new seed. It only holds sample data:

```powershell
Remove-Item -ErrorAction SilentlyContinue C:\Users\Comtech\HisabDO\conversation-management\data\app.db
```

**Check.** `pytest -q` prints `161 passed`.

## Step 3: Authentication (`chatbot/auth.py`, new file)

**Why.** This file answers one question: who is calling? The answer must come from something the caller can't fake.

In production the caller sends a Supabase access token. The code checks six things, and each one blocks a known attack:

| Check | Attack it blocks |
|---|---|
| Signature, with the algorithm fixed to HS256 | Forged tokens, and the "alg: none" trick |
| Expiry | Reusing an old or stolen token forever |
| Audience is `authenticated` | Tokens issued for a different purpose |
| Role is `authenticated` | The public "anon" key and service keys |
| Not an anonymous session | Sign-ins that have no real identity |
| The token's user ID is linked to a user in your database | Valid logins that have no business with you |

The `X-User-Id` header is ignored completely in production mode.

**Do this.** Create `chatbot/auth.py`:

```python
"""Authentication: work out WHO is calling, from a credential the caller can't forge.

The user's identity always comes from the credential. Nothing in the request
body or query string can choose whose data is read.

    AUTH_MODE=supabase  Authorization: Bearer <Supabase access token>
                        Checked: signature (HS256 only), expiry, audience,
                        role "authenticated", not an anonymous session, and the
                        token's user ID must be linked to a user in our database.
    AUTH_MODE=dev       X-User-Id: U-001   (no password - local development only;
                        Settings.validate() refuses it in production)
    anything else       401 for every request
"""

from __future__ import annotations

from uuid import UUID

import jwt

from .config import Settings
from .models import User
from .repository import RecordNotFound, Repository


class AuthError(Exception):
    """Authentication failed. The message is safe to show to the caller."""


def authenticate(
    settings: Settings, repo: Repository, authorization: str | None, x_user_id: str | None
) -> User:
    if settings.auth_mode == "supabase":
        # X-User-Id is deliberately ignored here, even if present.
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("Missing bearer token.")
        auth_id = _verify_supabase_token(token.strip(), settings)
        try:
            return repo.get_user_by_auth_id(auth_id)
        except RecordNotFound:
            # A valid login that isn't linked to any business yet.
            raise AuthError("This account has no access to HisabDo data.") from None

    if settings.auth_mode == "dev" and settings.allow_dev_auth and not settings.is_production:
        if not x_user_id:
            raise AuthError("Missing X-User-Id header (dev auth).")
        try:
            return repo.get_user(x_user_id)
        except RecordNotFound:
            raise AuthError("Unknown user.") from None

    raise AuthError("Authentication is not configured.")


def _verify_supabase_token(token: str, settings: Settings) -> str:
    try:
        claims = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],  # fixed list: blocks "alg: none" and algorithm switching
            audience=settings.supabase_jwt_audience,
            options={"require": ["exp", "sub", "aud"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("Session expired. Please sign in again.") from None
    except jwt.PyJWTError:
        raise AuthError("Invalid authentication token.") from None
    # Rejects the public "anon" key, service-role keys, and anonymous sign-ins.
    if claims.get("role") != "authenticated" or claims.get("is_anonymous"):
        raise AuthError("Invalid authentication token.")
    try:
        return str(UUID(str(claims["sub"])))
    except (ValueError, TypeError):
        raise AuthError("Invalid authentication token.") from None
```

**Ask your auth team one question before going live:** does the project sign tokens with a shared secret (HS256) or with public keys (JWKS)? This code handles the shared secret. If the project uses public keys, every real token will be rejected, which is safe but means login won't work until the check is changed.

## Step 4: Reporting periods (`chatbot/periods.py`, new file)

**Why.** At 01:00 on 1 October in Karachi it is still 30 September in UTC, and most servers run on UTC. If the app uses the server's date, a late-night invoice lands in the wrong month and a task becomes overdue a day late.

This file makes every "today" and every period boundary use the business's timezone. It also rejects unclear input (month 13, a range that ends before it starts, both styles at once) instead of guessing.

**Do this.** Create `chatbot/periods.py`:

```python
"""Reporting periods: whole calendar days in the business's reporting timezone.

Why this matters: at 01:00 on 1 October in Karachi it is still 30 September in
UTC. A server that uses its own (UTC) date would put that day's invoices in the
wrong month and mark tasks overdue a day late. Every "today" and every period
boundary in the app goes through this module instead.

Accepted inputs (one style per request):
    period=2026-09                   a calendar month
    start=2026-09-01&end=2026-09-15  a custom range, both days inclusive
    (nothing)                        the current month
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


class InvalidPeriod(ValueError):
    pass


@dataclass(frozen=True)
class Period:
    start: date  # inclusive
    end: date  # inclusive
    timezone: str

    def contains(self, day: date | None) -> bool:
        return day is not None and self.start <= day <= self.end


def local_today(timezone_name: str) -> date:
    """Today's date where the business is, not where the server is."""
    try:
        return datetime.now(ZoneInfo(timezone_name)).date()
    except (ZoneInfoNotFoundError, ValueError):
        raise InvalidPeriod(f"Unknown timezone {timezone_name!r}.") from None


def resolve_period(
    period: str | None, start: date | None, end: date | None, today: date, timezone_name: str, max_days: int = 366
) -> Period:
    if period and (start or end):
        raise InvalidPeriod("Use either 'period' or 'start' and 'end', not both.")
    if period:
        m = _MONTH.match(period.strip())
        if not m:
            raise InvalidPeriod("'period' must look like YYYY-MM, for example 2026-09.")
        year, month = int(m.group(1)), int(m.group(2))
        if not 2000 <= year <= 2100:
            raise InvalidPeriod("'period' year is out of range.")
        return Period(date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]), timezone_name)
    if start or end:
        if not (start and end):
            raise InvalidPeriod("Both 'start' and 'end' are required for a custom range.")
        if start > end:
            raise InvalidPeriod("'start' must be on or before 'end'.")
        if (end - start).days + 1 > max_days:
            raise InvalidPeriod(f"A custom range can be at most {max_days} days.")
        return Period(start, end, timezone_name)
    last = calendar.monthrange(today.year, today.month)[1]
    return Period(today.replace(day=1), today.replace(day=last), timezone_name)
```

---

# Part B: Semantic knowledge base

## The idea in two minutes

**Keyword matching** counts shared words. "kharcha kaise likhun?" and "How do I record an expense?" share none, so the score is 0 and the right answer is never found.

**An embedding** turns a text into a list of numbers (a vector) that represents its meaning. Texts with similar meaning get vectors that point in nearly the same direction, in any language.

**Cosine similarity** measures how closely two vectors point the same way: 1.0 means the same meaning, around 0 means unrelated.

**The relevance threshold** is the minimum score a passage needs to be used. Without it, search always returns the "nearest" passages, even for a biryani recipe, and the model is tempted to answer from them.

| Question | Best KB match | Score | With threshold 0.60 |
|---|---|---|---|
| "kharcha kaise likhun?" | "How do I record an expense?" | high | Used, and cited |
| "Give me a biryani recipe" | whatever is least unrelated | low | Rejected: "no verified information" |

The flow you are building:

```
question -> embed the question -> compare with every KB passage -> keep scores >= threshold
         -> put those passages in the prompt with their IDs -> model answers and cites [KB-001]
         -> validator removes any citation to an entry that was not retrieved
```

## Step 5: Knowledge base files and versioning (`kb/` folder and `chatbot/kb.py`)

**Why.** The chatbot may only state product facts that a person has confirmed. So the knowledge base lives in files that are reviewed like code, and three rules are enforced by the loader:

- **Verified only.** An entry is indexed only if it has `status: verified`, a named verifier and a date. Drafts can sit in the folder with no risk of being quoted.
- **Every entry has an ID** (`KB-001`), which the model cites and the user sees.
- **Every version is kept.** Each release has a version number, and the index stores them side by side, so going back is one command.

**Do this (1 of 2).** Copy the starter knowledge base. It contains the folder structure, a changelog, and four example entries that are all marked `draft`:

```powershell
Copy-Item -Recurse -Force C:\Users\Comtech\HisabDO\implementation-guide\reference\kb C:\Users\Comtech\HisabDO\conversation-management\kb
```

What you get:

| File | Purpose |
|---|---|
| `kb/v1/manifest.json` | The version number of this KB release |
| `kb/v1/faqs.json` | Question-and-answer entries |
| `kb/v1/docs/*.md` | Longer product documentation, split into sections by `##` headings |
| `kb/CHANGELOG.md` | What changed in each version |
| `kb/eval_questions.json` | Test questions for tuning the threshold in Step 14 |

**I did not write real product content.** I don't know HisabDo's real screens or prices, and inventing them would defeat the purpose. The drafts are placeholders for the product team to replace and verify.

**Do this (2 of 2).** Create `chatbot/kb.py`, which loads, validates and splits the files:

```python
"""Knowledge base files: load, validate, and split into chunks.

Layout (one folder per KB version, kept in git so every change is reviewable):

    kb/v1/manifest.json        {"kb_version": "1.0.0", "released_on": "...", "changes": "..."}
    kb/v1/faqs.json            [{"id": "KB-001", "question": ..., "answer": ..., "status": "verified", ...}]
    kb/v1/docs/<name>.md       product documentation with a header block (see below)

A doc file starts with a header between two '---' lines:

    ---
    id: KB-101
    title: Recording an expense
    status: verified
    verified_by: Product team
    verified_on: 2026-10-13
    source: HisabDo user guide, section 4
    ---
    ## Section heading
    Text...

Only entries with status "verified" AND a named verifier AND a date are ever
indexed. A draft can sit in the folder without any risk of the chatbot quoting it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

MAX_CHUNK_CHARS = 1200
_ID = re.compile(r"^KB-\d{3,}$")


class KBError(ValueError):
    pass


@dataclass(frozen=True)
class KBEntry:
    id: str
    title: str
    body: str  # FAQ: the answer. Doc: the markdown text.
    kind: str  # "faq" | "doc"
    status: str  # "verified" | "draft"
    verified_by: str = ""
    verified_on: str = ""
    source: str = ""
    category: str = ""

    @property
    def is_verified(self) -> bool:
        return self.status == "verified" and bool(self.verified_by.strip()) and bool(self.verified_on.strip())


@dataclass(frozen=True)
class KBChunk:
    entry_id: str
    chunk_no: int
    title: str
    section: str
    text: str
    source: str
    kb_version: str


def load_kb(version_dir: str | Path) -> tuple[str, list[KBEntry]]:
    """Read one KB version folder. Returns (kb_version, entries) and raises KBError on any problem."""
    root = Path(version_dir)
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        version = str(manifest["kb_version"])
    except (OSError, KeyError, json.JSONDecodeError) as e:
        raise KBError(f"{root}/manifest.json is missing or has no kb_version: {e}") from None

    entries: list[KBEntry] = []
    faq_file = root / "faqs.json"
    if faq_file.exists():
        try:
            raw_faqs = json.loads(faq_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise KBError(f"{faq_file}: invalid JSON: {e}") from None
        for f in raw_faqs:
            entries.append(KBEntry(
                id=str(f.get("id", "")), title=str(f.get("question", "")).strip(), body=str(f.get("answer", "")).strip(),
                kind="faq", status=str(f.get("status", "draft")), verified_by=str(f.get("verified_by", "")),
                verified_on=str(f.get("verified_on", "")), source=str(f.get("source", "")), category=str(f.get("category", "")),
            ))
    for path in sorted((root / "docs").glob("*.md")) if (root / "docs").exists() else []:
        entries.append(_parse_doc(path))

    _validate(entries)
    return version, entries


def _parse_doc(path: Path) -> KBEntry:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise KBError(f"{path}: missing the '---' header block")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
    return KBEntry(
        id=meta.get("id", ""), title=meta.get("title", ""), body=m.group(2).strip(), kind="doc",
        status=meta.get("status", "draft"), verified_by=meta.get("verified_by", ""),
        verified_on=meta.get("verified_on", ""), source=meta.get("source", ""), category=meta.get("category", ""),
    )


def _validate(entries: list[KBEntry]) -> None:
    problems, seen = [], set()
    for e in entries:
        label = e.id or f"(no id: {e.title[:40]!r})"
        if not _ID.match(e.id):
            problems.append(f"{label}: id must look like KB-001")
        if e.id in seen:
            problems.append(f"{label}: duplicate id")
        seen.add(e.id)
        if not e.title or not e.body:
            problems.append(f"{label}: empty title/question or body/answer")
        if e.status not in ("verified", "draft"):
            problems.append(f"{label}: status must be 'verified' or 'draft'")
        if e.status == "verified":
            if not e.verified_by.strip():
                problems.append(f"{label}: verified entries need verified_by")
            try:
                date.fromisoformat(e.verified_on)
            except ValueError:
                problems.append(f"{label}: verified entries need verified_on as YYYY-MM-DD")
    if problems:
        raise KBError("Knowledge base problems:\n  - " + "\n  - ".join(problems))


def chunk_entries(kb_version: str, entries: list[KBEntry]) -> list[KBChunk]:
    """Split VERIFIED entries into retrieval-sized chunks. Drafts are skipped."""
    chunks: list[KBChunk] = []
    for e in entries:
        if not e.is_verified:
            continue
        if e.kind == "faq":
            parts = [("", f"Q: {e.title}\nA: {e.body}")]
        else:
            parts = _split_doc(e.body)
        for n, (section, text) in enumerate(parts, 1):
            chunks.append(KBChunk(e.id, n, e.title, section, text, e.source, kb_version))
    return chunks


def _split_doc(body: str) -> list[tuple[str, str]]:
    """Split on '## ' headings, then on paragraphs if a section is still too long."""
    sections: list[tuple[str, str]] = []
    heading, lines = "", []
    for line in body.splitlines():
        if line.startswith("## "):
            if "".join(lines).strip():
                sections.append((heading, "\n".join(lines).strip()))
            heading, lines = line[3:].strip(), []
        else:
            lines.append(line)
    if "".join(lines).strip():
        sections.append((heading, "\n".join(lines).strip()))

    out: list[tuple[str, str]] = []
    for heading, text in sections:
        if len(text) <= MAX_CHUNK_CHARS:
            out.append((heading, text))
            continue
        current = ""
        for para in re.split(r"\n\s*\n", text):
            if current and len(current) + len(para) + 2 > MAX_CHUNK_CHARS:
                out.append((heading, current.strip()))
                current = ""
            current += para + "\n\n"
        if current.strip():
            out.append((heading, current.strip()))
    return out
```

## Step 6: Embeddings (`chatbot/embeddings.py`, new file)

**Why.** This is the piece that replaces keyword matching. It sits behind a small interface (`Embedder`), so tests can use a fake and the real one can be swapped later.

Two details matter:

- **Documents and questions are embedded differently** (`RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY`). The model is trained so that a question lands near the passage that answers it.
- **Failures raise one specific error**, `EmbeddingUnavailable`. Everything that calls this code catches it and degrades safely. The chatbot must never crash because an embedding call failed.

**Do this.** Create `chatbot/embeddings.py`:

```python
"""Embeddings: turn text into a vector so that texts with similar MEANING are close together.

"kharcha kaise likhun?" and "How do I record an expense?" share no words, so
keyword matching scores them 0. Their embedding vectors point in nearly the same
direction, so semantic search finds the match.

Behind a small protocol so tests can use a fake and no API key.
"""

from __future__ import annotations

import math
import os
import time
from typing import Protocol

BATCH_SIZE = 50


class EmbeddingUnavailable(RuntimeError):
    """The embedding service can't be used right now. Callers must degrade safely, never crash."""


class Embedder(Protocol):
    model: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def normalize(vector: list[float]) -> list[float]:
    """Scale to length 1, so cosine similarity becomes a plain dot product."""
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector] if norm else list(vector)


def cosine(a: list[float], b: list[float]) -> float:
    """Similarity of two NORMALIZED vectors: 1.0 = same meaning, about 0 = unrelated."""
    return sum(x * y for x, y in zip(a, b))


class GeminiEmbedder:
    """Google Gemini embeddings. Reads GEMINI_API_KEY from the environment."""

    def __init__(self, model: str | None = None, dim: int = 768, client=None) -> None:
        self.model = model or os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")
        self.dim = dim
        try:
            from google import genai

            self.client = client or genai.Client()
        except Exception as e:  # no key configured, package missing
            raise EmbeddingUnavailable("Embeddings are not configured (GEMINI_API_KEY).") from e

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            out += self._embed(texts[i : i + BATCH_SIZE], "RETRIEVAL_DOCUMENT")
            if i + BATCH_SIZE < len(texts):
                time.sleep(1)  # stay under free-tier rate limits when indexing a large KB
        return out

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        from google.genai import errors, types

        try:
            # Documents and queries use different task types: the model is trained so that a
            # QUESTION lands near the passage that ANSWERS it, not near similar questions.
            response = self.client.models.embed_content(
                model=self.model,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=self.dim),
            )
        except errors.APIError as e:
            raise EmbeddingUnavailable(f"Embedding request failed (HTTP {e.code}).") from e
        except Exception as e:  # network errors
            raise EmbeddingUnavailable("Could not reach the embedding service.") from e
        vectors = [normalize(list(e.values)) for e in response.embeddings]
        if len(vectors) != len(texts):
            raise EmbeddingUnavailable("Embedding service returned the wrong number of vectors.")
        return vectors
```

## Step 7: Vector storage (`chatbot/vector_store.py`, new file)

**Why.** Vectors have to be stored somewhere and searched. This uses the SQLite database you already have, which is enough for a few thousand passages.

The versioning works like this: `save_version` stores a version without making it live, and `activate` switches the live version in one write. So a half-built index is never served, and rollback needs no re-indexing.

Note vectors are stored per business, and every query filters on `business_id`.

**Do this.** Create `chatbot/vector_store.py`:

```python
"""Vector storage for the knowledge base and for notes, in the app's SQLite database.

KB chunks are stored per kb_version, and exactly one version is "active".
Building a new version never touches the active one, so:
  * a half-built index is never served, and
  * rolling back is one command (activate the previous version).

For a few thousand chunks a full scan with a dot product is fast enough. When
the KB outgrows that, swap this class for pgvector in Supabase; nothing else changes.
"""

from __future__ import annotations

import hashlib
from array import array

from .embeddings import cosine
from .kb import KBChunk
from .repository import Repository

SCHEMA = """
CREATE TABLE IF NOT EXISTS kb_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kb_version TEXT NOT NULL, entry_id TEXT NOT NULL, chunk_no INTEGER NOT NULL,
    title TEXT NOT NULL, section TEXT NOT NULL DEFAULT '', text TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '', model TEXT NOT NULL, embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_kb_chunks_version ON kb_chunks(kb_version);
CREATE TABLE IF NOT EXISTS kb_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS note_vectors (
    note_id TEXT PRIMARY KEY, business_id TEXT NOT NULL, content_hash TEXT NOT NULL,
    model TEXT NOT NULL, embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_note_vectors_biz ON note_vectors(business_id);
"""


def _pack(vector: list[float]) -> bytes:
    return array("f", vector).tobytes()


def _unpack(blob: bytes) -> list[float]:
    values = array("f")
    values.frombytes(blob)
    return values.tolist()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class VectorStore:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        with repo.connect() as conn:
            conn.executescript(SCHEMA)

    # --- knowledge base ---------------------------------------------------------------

    def save_version(self, kb_version: str, chunks: list[KBChunk], vectors: list[list[float]], model: str) -> None:
        """Store (or rebuild) one KB version. Does NOT make it active."""
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        with self.repo.connect() as conn:
            conn.execute("DELETE FROM kb_chunks WHERE kb_version = ?", (kb_version,))
            conn.executemany(
                "INSERT INTO kb_chunks (kb_version, entry_id, chunk_no, title, section, text, source, model, embedding)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(kb_version, c.entry_id, c.chunk_no, c.title, c.section, c.text, c.source, model, _pack(v))
                 for c, v in zip(chunks, vectors)],
            )

    def versions(self) -> dict[str, int]:
        with self.repo.connect() as conn:
            rows = conn.execute("SELECT kb_version, COUNT(*) AS n FROM kb_chunks GROUP BY kb_version").fetchall()
        return {r["kb_version"]: r["n"] for r in rows}

    def activate(self, kb_version: str) -> None:
        if kb_version not in self.versions():
            raise ValueError(f"KB version {kb_version!r} has not been indexed")
        with self.repo.connect() as conn:
            conn.execute(
                "INSERT INTO kb_meta (key, value) VALUES ('active_version', ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value", (kb_version,),
            )

    def active_version(self) -> str | None:
        with self.repo.connect() as conn:
            row = conn.execute("SELECT value FROM kb_meta WHERE key = 'active_version'").fetchone()
        return row["value"] if row else None

    def active_model(self) -> str | None:
        version = self.active_version()
        if version is None:
            return None
        with self.repo.connect() as conn:
            row = conn.execute("SELECT model FROM kb_chunks WHERE kb_version = ? LIMIT 1", (version,)).fetchone()
        return row["model"] if row else None

    def search(self, query_vector: list[float], top_k: int) -> list[tuple[KBChunk, float]]:
        """The top_k chunks of the ACTIVE version, most similar first, with their scores."""
        version = self.active_version()
        if version is None:
            return []
        with self.repo.connect() as conn:
            rows = conn.execute("SELECT * FROM kb_chunks WHERE kb_version = ?", (version,)).fetchall()
        scored = [
            (KBChunk(r["entry_id"], r["chunk_no"], r["title"], r["section"], r["text"], r["source"], r["kb_version"]),
             cosine(query_vector, _unpack(r["embedding"])))
            for r in rows
        ]
        scored.sort(key=lambda cs: cs[1], reverse=True)
        return scored[:top_k]

    # --- note vectors (always scoped to one business) -----------------------------------

    def note_hashes(self, business_id: str, model: str) -> dict[str, str]:
        with self.repo.connect() as conn:
            rows = conn.execute(
                "SELECT note_id, content_hash FROM note_vectors WHERE business_id = ? AND model = ?", (business_id, model)
            ).fetchall()
        return {r["note_id"]: r["content_hash"] for r in rows}

    def save_note_vectors(self, business_id: str, model: str, items: list[tuple[str, str, list[float]]]) -> None:
        """items = [(note_id, content_hash, vector)]"""
        with self.repo.connect() as conn:
            conn.executemany(
                "INSERT INTO note_vectors (note_id, business_id, content_hash, model, embedding) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(note_id) DO UPDATE SET business_id = excluded.business_id,"
                " content_hash = excluded.content_hash, model = excluded.model, embedding = excluded.embedding",
                [(note_id, business_id, h, model, _pack(v)) for note_id, h, v in items],
            )

    def delete_note_vectors(self, business_id: str, note_ids: list[str]) -> None:
        with self.repo.connect() as conn:
            conn.executemany(
                "DELETE FROM note_vectors WHERE business_id = ? AND note_id = ?", [(business_id, n) for n in note_ids]
            )

    def note_vectors(self, business_id: str, model: str) -> dict[str, list[float]]:
        with self.repo.connect() as conn:
            rows = conn.execute(
                "SELECT note_id, embedding FROM note_vectors WHERE business_id = ? AND model = ?", (business_id, model)
            ).fetchall()
        return {r["note_id"]: _unpack(r["embedding"]) for r in rows}
```

## Step 8: Retrieval with a threshold and a safe fallback (`chatbot/retrieval.py`, new file)

**Why.** This file turns "search" into a decision. Every retrieval ends in exactly one of four statuses, and the chatbot behaves differently for each:

| Status | Meaning | What the chatbot does |
|---|---|---|
| `ok` | At least one passage scored at or above the threshold | Answers from it and cites it |
| `no_match` | Nothing reached the threshold | Says it has no verified information |
| `empty` | No KB version is live | Same as `no_match` |
| `unavailable` | The embedding service failed, or the index was built with a different model | Says product information is temporarily unavailable |

That table is the safe fallback. There is no path where a failure turns into a guessed answer.

`NoteIndex` applies the same idea to the notes in your business data, replacing the keyword-overlap scoring in `context_builder.py`. If embeddings are down it returns `None`, and the context builder falls back to keywords. Keyword matching stays only as that fallback.

**Do this.** Create `chatbot/retrieval.py`:

```python
"""Semantic retrieval with a relevance threshold and a safe fallback.

Every retrieval ends in exactly one status, and the chatbot behaves differently for each:

    ok           at least one KB entry scored >= threshold  -> answer from it and cite it
    no_match     nothing reached the threshold               -> say there is no verified information
    empty        no KB version is active                     -> same as no_match
    unavailable  the embedding service failed                -> say product info is temporarily unavailable

The threshold is the difference between "retrieval" and "always return the
nearest thing": without it, a biryani question still gets the 4 least-unrelated
passages, and the model is tempted to answer from them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .embeddings import Embedder, EmbeddingUnavailable, cosine
from .models import Note
from .vector_store import VectorStore, text_hash

MAX_SECTIONS_PER_SOURCE = 2


@dataclass(frozen=True)
class KBSource:
    """One KB entry that passed the threshold, with the passages that matched."""

    id: str
    title: str
    source: str
    kb_version: str
    score: float  # best passage score, 0..1
    passages: tuple[tuple[str, str], ...]  # (section heading, text)


@dataclass(frozen=True)
class RetrievalResult:
    status: str  # ok | no_match | empty | unavailable
    sources: tuple[KBSource, ...] = ()
    kb_version: str | None = None
    best_score: float | None = None  # highest score seen, even if below the threshold (for tuning)
    threshold: float = 0.0
    query_vector: list[float] | None = field(default=None, repr=False, compare=False)


class KBRetriever:
    def __init__(self, store: VectorStore, embedder: Embedder, threshold: float = 0.60, top_k: int = 4) -> None:
        self.store = store
        self.embedder = embedder
        self.threshold = threshold
        self.top_k = top_k

    def retrieve(self, question: str) -> RetrievalResult:
        version = self.store.active_version()
        try:
            query_vector = self.embedder.embed_query(question)
        except EmbeddingUnavailable:
            return RetrievalResult("unavailable", kb_version=version, threshold=self.threshold)
        if version is None:
            return RetrievalResult("empty", threshold=self.threshold, query_vector=query_vector)
        if self.store.active_model() != self.embedder.model:
            # Vectors from different models are not comparable; refusing is safer than wrong matches.
            return RetrievalResult("unavailable", kb_version=version, threshold=self.threshold, query_vector=query_vector)

        hits = self.store.search(query_vector, self.top_k * 3)
        best = hits[0][1] if hits else None
        grouped: dict[str, list] = {}
        for chunk, score in hits:
            if score >= self.threshold:
                grouped.setdefault(chunk.entry_id, []).append((chunk, score))

        sources = []
        for entry_id, items in grouped.items():
            items = items[:MAX_SECTIONS_PER_SOURCE]
            first = items[0][0]
            sources.append(KBSource(
                id=entry_id, title=first.title, source=first.source, kb_version=first.kb_version,
                score=round(items[0][1], 4), passages=tuple((c.section, c.text) for c, _ in items),
            ))
        sources = sorted(sources, key=lambda s: s.score, reverse=True)[: self.top_k]
        return RetrievalResult(
            "ok" if sources else "no_match", tuple(sources), version,
            round(best, 4) if best is not None else None, self.threshold, query_vector,
        )


class NoteIndex:
    """Semantic search over ONE business's notes, replacing keyword overlap.

    Vectors are created lazily: each search first embeds any note that is new or
    whose text changed, and drops vectors of deleted notes. Returns None when the
    embedding service is unavailable, so the caller can fall back to keyword matching.
    """

    def __init__(self, store: VectorStore, embedder: Embedder, threshold: float = 0.55, top_k: int = 5) -> None:
        self.store = store
        self.embedder = embedder
        self.threshold = threshold
        self.top_k = top_k

    def rank(self, business_id: str, notes: list[Note], query_vector: list[float] | None) -> list[Note] | None:
        if query_vector is None:
            return None
        wrong_tenant = [n.id for n in notes if n.business_id != business_id]
        if wrong_tenant:  # defence in depth: never index or return another business's notes
            raise ValueError(f"notes from another business passed to NoteIndex: {wrong_tenant}")
        try:
            self._sync(business_id, notes)
        except EmbeddingUnavailable:
            return None
        vectors = self.store.note_vectors(business_id, self.embedder.model)
        scored = [(cosine(query_vector, vectors[n.id]), n) for n in notes if n.id in vectors]
        scored = [(s, n) for s, n in scored if s >= self.threshold]
        scored.sort(key=lambda sn: (-sn[0], -sn[1].created_at.timestamp()))
        return [n for _, n in scored[: self.top_k]]

    def _sync(self, business_id: str, notes: list[Note]) -> None:
        stored = self.store.note_hashes(business_id, self.embedder.model)
        current = {n.id: text_hash(n.content) for n in notes}
        stale = [n for n in notes if stored.get(n.id) != current[n.id]]
        if stale:
            vectors = self.embedder.embed_documents([n.content for n in stale])
            self.store.save_note_vectors(
                business_id, self.embedder.model, [(n.id, current[n.id], v) for n, v in zip(stale, vectors)]
            )
        deleted = [note_id for note_id in stored if note_id not in current]
        if deleted:
            self.store.delete_note_vectors(business_id, deleted)


def build_index(store: VectorStore, embedder: Embedder, kb_dir) -> tuple[str, int, int]:
    """Embed and store one KB version folder. Returns (kb_version, chunks indexed, drafts skipped).

    Does not activate the version; call store.activate(version) when it should go live.
    """
    from .kb import chunk_entries, load_kb

    version, entries = load_kb(kb_dir)
    chunks = chunk_entries(version, entries)
    if chunks:
        # Title and section are embedded with the text, so a short passage keeps its topic.
        vectors = embedder.embed_documents([f"{c.title}\n{c.section}\n{c.text}".strip() for c in chunks])
        store.save_version(version, chunks, vectors, embedder.model)
    return version, len(chunks), sum(1 for e in entries if not e.is_verified)
```

## Step 9: Tell the model the rules (`chatbot/prompts.py` and `chatbot/grounding.py`)

**Why.** Retrieval only helps if the model is told what to do with it. Three rules are added to the prompt:

- Product questions may be answered only from `<knowledge_base>`, with a citation.
- If the status is `no_match`, `empty` or `unavailable`, say so. Don't answer from general knowledge.
- If the business is demo data, say so once when quoting figures.

The citation checker also has to recognise `[KB-012]`, not only `[C-001]`. It already removes citations to records the model wasn't given, so it now does the same for KB entries.

**Do this (1 of 2).** Edit `chatbot/prompts.py`:

**Edit 1 of 2.** Find this text (it can be part of a line):

```python
member, C- customer, R- receivable, P- payable, T- task, N- note.
```

Replace it with:

```python
member, C- customer, R- receivable, P- payable, T- task, N- note, KB- verified \
knowledge-base entry about the HisabDo product.
```

**Edit 2 of 2.** Find this text (it can be part of a line):

```python
- Be concise and practical. Dates are YYYY-MM-DD;
```

Replace it with:

```python
- Questions about HisabDo itself (its features, how to do something in the app, \
pricing, product policies) may be answered ONLY from <knowledge_base>. Cite the \
kb_source id you used, e.g. "You can export a ledger as PDF [KB-012]." Don't describe \
screens, menus or steps that aren't written in a passage.
- If <knowledge_base> has status "no_match" or "empty", say you don't have verified \
information about that yet and suggest contacting HisabDo support. Do not answer \
from general knowledge of what apps like this usually do. If its status is \
"unavailable", say product information is temporarily unavailable and to try again \
shortly. Questions about the user's own business data are unaffected by this.
- If <business> has data_mode="demo", its records are sample data, not a real \
customer's books: say so once when you quote figures from it.
- Be concise and practical. Dates are YYYY-MM-DD;
```

**Do this (2 of 2).** Edit `chatbot/grounding.py`:

**The edit.** Find this text (it can be part of a line):

```python
_INLINE_CITATION = re.compile(r"\[([A-Z]-\d{3,})\]")
```

Replace it with:

```python
_INLINE_CITATION = re.compile(r"\[([A-Z]{1,2}-\d{3,})\]")  # [C-001] records and [KB-012] knowledge base
```

## Step 10: Put retrieved knowledge into the context (`chatbot/context_builder.py`)

**Why.** The context builder decides what the model sees. These edits do four things:

- Accept the retrieval result and render it as a `<knowledge_base>` block, with each source's ID, title and origin.
- Add the KB IDs to the list of things the model is allowed to cite.
- Use semantic ranking for notes when available, with keyword overlap as the fallback.
- Label the business as `demo` or `actual`.

**Do this.** Edit `chatbot/context_builder.py`:

**Edit 1 of 12.** Find this text (it can be part of a line):

```python
from datetime import date, timedelta
```

Replace it with:

```python
from datetime import date, timedelta
from typing import Callable
```

**Edit 2 of 12.** Find this text (it can be part of a line):

```python
from .repository import Repository
```

Replace it with:

```python
from .repository import Repository
from .retrieval import RetrievalResult
```

**Edit 3 of 12.** Find this text (it can be part of a line):

```python
    included: dict[str, list[str]] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)
```

Replace it with:

```python
    included: dict[str, list[str]] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)
    kb_ids: list[str] = field(default_factory=list)  # knowledge-base entries shown to the model
```

**Edit 4 of 12.** Find this text (it can be part of a line):

```python
        focus_customer_ids: list[str] | None = None,
    ) -> ContextBundle:
```

Replace it with:

```python
        focus_customer_ids: list[str] | None = None,
        kb: RetrievalResult | None = None,
        note_ranker: Callable[[list[Note]], list[Note] | None] | None = None,
    ) -> ContextBundle:
```

**Edit 5 of 12.** Find this text (it can be part of a line):

```python
        if terms and (_NOTE_INTENT.search(q) or not matched):
            scored = [(len(terms & _keywords(n.content.lower())), n) for n in notes]
```

Replace it with:

```python
        semantic = note_ranker(notes) if note_ranker else None
        if semantic is not None:
            # Semantic search: ranked by meaning, so "udhaar limit" finds a note about "credit limit".
            chosen_notes += semantic
        elif terms and (_NOTE_INTENT.search(q) or not matched):
            # Fallback only (embeddings unavailable): keyword overlap.
            scored = [(len(terms & _keywords(n.content.lower())), n) for n in notes]
```

**Edit 6 of 12.** Find this text (it can be part of a line):

```python
            _render_notes(chosen_notes, user_names, customer_names),
            _render_scope(
```

Replace it with:

```python
            _render_notes(chosen_notes, user_names, customer_names),
            _render_kb(kb),
            _render_scope(
```

**Edit 7 of 12.** Find this text (it can be part of a line):

```python
"\n".join(sections) + "\n</business_context>"
```

Replace it with:

```python
"\n".join(s for s in sections if s) + "\n</business_context>"
```

**Edit 8 of 12.** Find this text (it can be part of a line):

```python
            | {n.id for n in chosen_notes}
        )
```

Replace it with:

```python
            | {n.id for n in chosen_notes}
            | kb_ids
        )
```

**Edit 9 of 12.** Find this text (it can be part of a line):

```python
        source_ids = (
            {user.id, business.id}
```

Replace it with:

```python
        kb_ids = {s.id for s in kb.sources} if kb is not None and kb.status == "ok" else set()
        source_ids = (
            {user.id, business.id}
```

**Edit 10 of 12.** Find this text (it can be part of a line):

```python
            totals={
                "customers": len(customers),
```

Replace it with:

```python
            kb_ids=sorted(kb_ids),
            totals={
                "customers": len(customers),
```

**Edit 11 of 12.** Find this text (it can be part of a line):

```python
    lines = [f"<business {_attrs(id=b.id, name=b.name, industry=b.industry, currency=b.currency)}>"]
```

Replace it with:

```python
    mode = "demo" if b.is_demo else "actual"
    lines = [f"<business {_attrs(id=b.id, name=b.name, industry=b.industry, currency=b.currency, data_mode=mode)}>"]
```

**Edit 12 of 12.** Find this text (it can be part of a line):

```python
def _render_scope(**counts: tuple[int, int]) -> str:
```

Replace it with:

```python
def _render_kb(kb: RetrievalResult | None) -> str:
    """Verified product knowledge that passed the relevance threshold, or an explicit 'nothing found'."""
    if kb is None:
        return ""
    if kb.status != "ok":
        return f'<knowledge_base status="{kb.status}"/>'
    rows = [f'<knowledge_base status="ok" version={quoteattr(kb.kb_version or "")} '
            'note="Verified HisabDo product information. Cite the id of each kb_source you use.">']
    for s in kb.sources:
        rows.append(f"  <kb_source {_attrs(id=s.id, title=s.title, source=s.source, relevance=f'{s.score:.2f}')}>")
        for section, text in s.passages:
            tag = f"<passage {_attrs(section=section)}>" if section else "<passage>"
            rows.append(f"    {tag}{escape(text)}</passage>")
        rows.append("  </kb_source>")
    rows.append("</knowledge_base>")
    return "\n".join(rows)


def _render_scope(**counts: tuple[int, int]) -> str:
```

## Step 11: Run retrieval on every question (`chatbot/service.py`)

**Why.** The service is where one chat turn is orchestrated. These edits:

- Run retrieval before building the context. If no retriever is configured, the status is `unavailable`, never "no knowledge base block at all". That keeps the fallback rule active even when embeddings aren't set up.
- Use the business's local date for "today" (the Step 4 fix).
- Return the KB entries the answer actually cited. That is the source attribution.

**Do this.** Edit `chatbot/service.py`:

**Edit 1 of 7.** Find this text (it can be part of a line):

```python
from .prompts import build_system
```

Replace it with:

```python
from .periods import local_today
from .prompts import build_system
from .retrieval import KBRetriever, NoteIndex, RetrievalResult
```

**Edit 2 of 7.** Find this text (it can be part of a line):

```python
    context_sources: dict[str, list[str]]
    context_totals: dict[str, int]
```

Replace it with:

```python
    context_sources: dict[str, list[str]]
    context_totals: dict[str, int]
    kb: RetrievalResult | None = None
    sources: list[dict] = field(default_factory=list)  # KB entries the answer actually cited
```

**Edit 3 of 7.** Find this text (it can be part of a line):

```python
from dataclasses import dataclass
```

Replace it with:

```python
from dataclasses import dataclass, field
```

**Edit 4 of 7.** Find this text (it can be part of a line):

```python
        today: date | None = None,
    ) -> None:
        self.builder = builder
        self.llm = llm
        self.conversations = conversations
        self._today = today
```

Replace it with:

```python
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
```

**Edit 5 of 7.** Find this text (it can be part of a line):

```python
        return self._today or date.today()
```

Replace it with:

```python
        # The business's local date, not the server's: decides what is "overdue" and "today".
        return self._today or local_today(self.timezone)
```

**Edit 6 of 7.** Find this text (it can be part of a line):

```python
            bundle = self.builder.build(user.id, question, self.today(), conv.focus_customer_ids)
```

Replace it with:

```python
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
```

**Edit 7 of 7.** Find this text (it can be part of a line):

```python
                context_sources=bundle.included,
                context_totals=bundle.totals,
            )
```

Replace it with:

```python
                context_sources=bundle.included,
                context_totals=bundle.totals,
                kb=kb,
                sources=[
                    {"id": s.id, "title": s.title, "source": s.source, "kb_version": s.kb_version, "relevance": s.score}
                    for s in kb.sources if s.id in answer.citations
                ],
            )
```

**Check.** `pytest -q` still prints `161 passed`.

---

# Wiring it together

## Step 12: Connect everything in `app.py`

**Why.** This is where the security work takes effect. After these edits:

- **Every data route** gets its user from `authenticate()`, not from a header it trusts.
- **Unknown query parameters are rejected** (`only_params`), so `?business_id=B-002` returns 400 and is never silently ignored. The error does not repeat the parameter back.
- **Demo businesses are blocked** unless `ALLOW_DEMO_DATA` is on, and every response says `data_mode`.
- **Financial responses are never cached** (`Cache-Control: no-store`).
- **API docs are hidden in production**, and the demo user list exists only in dev mode.
- **A report endpoint** returns invoices and bills for a period, using Step 4's rules.
- **Chat responses include `sources` and `knowledge_base`**: what was cited, the KB version, the best score and the threshold.

**Do this (1 of 4).** Edit `app.py`:

**Edit 1 of 14.** Find this text (it can be part of a line):

```python
from chatbot import schemas
```

Replace it with:

```python
from chatbot import schemas
from chatbot.auth import AuthError, authenticate
from chatbot.config import Settings
```

**Edit 2 of 14.** Find this text (it can be part of a line):

```python
from chatbot.conversations import
```

Replace it with:

```python
from chatbot.embeddings import Embedder, GeminiEmbedder
from chatbot.conversations import
```

**Edit 3 of 14.** Find this text (it can be part of a line):

```python
from chatbot.models import User
```

Replace it with:

```python
from chatbot.models import User
from chatbot.periods import InvalidPeriod, local_today, resolve_period
```

**Edit 4 of 14.** Find this text (it can be part of a line):

```python
from chatbot.service import ChatReply, ChatService
```

Replace it with:

```python
from chatbot.retrieval import KBRetriever, NoteIndex
from chatbot.service import ChatReply, ChatService
from chatbot.vector_store import VectorStore
```

**Edit 5 of 14.** Find this text (it can be part of a line):

```python
    conversations: ConversationStore | None = None,
) -> FastAPI:
    app = FastAPI(title="Business-aware chatbot")
    builder = ContextBuilder(repo)
    conversations = conversations or ConversationStore(repo)
    state: dict = {}

    def current_date() -> date:
        return today or date.today()

    def chat_service() -> ChatService:
        if "chat" not in state:  # lazy: CRUD works without AI credentials
            try:
                state["chat"] = ChatService(builder, llm_factory(), conversations, today=today)
            except Exception as e:  # e.g. no API key configured
                raise LLMUnavailable("The AI assistant is not configured on this server.") from e
        return state["chat"]

    def current_user(x_user_id: str | None = Header(default=None)) -> User:
        if not x_user_id:
            raise HTTPException(401, "Missing X-User-Id header")
        try:
            return repo.get_user(x_user_id)
        except RecordNotFound:
            raise HTTPException(401, "Unknown user") from None
```

Replace it with:

```python
    conversations: ConversationStore | None = None,
    settings: Settings | None = None,
    embedder_factory: Callable[[], Embedder] | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.validate()  # refuse to start with an unsafe configuration
    # API documentation is not public in production.
    docs = {} if not settings.is_production else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title="Business-aware chatbot", **docs)
    builder = ContextBuilder(repo)
    conversations = conversations or ConversationStore(repo)
    state: dict = {}

    def current_date() -> date:
        return today or local_today(settings.reporting_timezone)

    def knowledge() -> tuple[KBRetriever | None, NoteIndex | None]:
        """Semantic search components, or (None, None) when embeddings aren't configured."""
        if "kb" not in state:
            try:
                factory = embedder_factory or (lambda: GeminiEmbedder(settings.embedding_model, settings.embedding_dim))
                embedder, store = factory(), VectorStore(repo)
                state["kb"] = (KBRetriever(store, embedder, settings.kb_threshold, settings.kb_top_k),
                               NoteIndex(store, embedder, settings.note_threshold))
            except Exception:  # no key: the chatbot still works, and says product info is unavailable
                state["kb"] = (None, None)
        return state["kb"]

    def chat_service() -> ChatService:
        if "chat" not in state:  # lazy: CRUD works without AI credentials
            try:
                llm = llm_factory()
            except Exception as e:  # e.g. no API key configured
                raise LLMUnavailable("The AI assistant is not configured on this server.") from e
            retriever, note_index = knowledge()
            state["chat"] = ChatService(builder, llm, conversations, today=today, retriever=retriever,
                                        note_index=note_index, timezone=settings.reporting_timezone)
        return state["chat"]

    def current_user(
        authorization: str | None = Header(default=None), x_user_id: str | None = Header(default=None)
    ) -> User:
        """AUTHENTICATION (who is calling) then the demo-data gate. Every data route depends on this."""
        try:
            user = authenticate(settings, repo, authorization, x_user_id)
        except AuthError as e:
            raise HTTPException(401, str(e), headers={"WWW-Authenticate": "Bearer"}) from None
        if repo.get_business(user.business_id).is_demo and not settings.allow_demo_data:
            raise HTTPException(403, "Demo data is disabled on this server.")
        return user

    def only_params(*allowed: str):
        """Reject any query parameter that isn't expected, so nobody can pass user_id or business_id."""
        def check(request: Request) -> None:
            unexpected = sorted(set(request.query_params.keys()) - set(allowed))
            if unexpected:
                raise HTTPException(400, "This request contains a parameter that is not allowed.")
        return Depends(check)

    def data_mode(user: User) -> str:
        return "demo" if repo.get_business(user.business_id).is_demo else "actual"

    @app.middleware("http")
    async def no_store(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"  # financial data must never be cached
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response
```

**Edit 6 of 14.** Find this text (it can be part of a line):

```python
    @app.exception_handler(LLMUnavailable)
```

Replace it with:

```python
    @app.exception_handler(InvalidPeriod)
    def _bad_period(_: Request, e: InvalidPeriod) -> JSONResponse:
        return JSONResponse({"detail": str(e)}, status_code=422)

    @app.exception_handler(LLMUnavailable)
```

**Edit 7 of 14.** Find this text (it can be part of a line):

```python
        @app.get(f"/api/{kind}", tags=[kind], name=f"list_{kind}")
```

Replace it with:

```python
        @app.get(f"/api/{kind}", tags=[kind], name=f"list_{kind}", dependencies=[only_params()])
```

**Edit 8 of 14.** Find this text (it can be part of a line):

```python
            "context": {"included": reply.context_sources, "totals": reply.context_totals},
        }
```

Replace it with:

```python
            "context": {"included": reply.context_sources, "totals": reply.context_totals},
            # Source attribution: the verified KB entries this answer cited.
            "sources": reply.sources,
            "knowledge_base": {
                "status": reply.kb.status if reply.kb else "unavailable",
                "version": reply.kb.kb_version if reply.kb else None,
                "best_score": reply.kb.best_score if reply.kb else None,
                "threshold": reply.kb.threshold if reply.kb else None,
            },
            "data_mode": data_mode(user),
        }
```

**Edit 9 of 14.** Find this text (it can be part of a line):

```python
    def reply_out(reply: ChatReply) -> dict:
```

Replace it with:

```python
    def reply_out(reply: ChatReply, user: User) -> dict:
```

**Edit 10 of 14.** Find this text (it can be part of a line):

```python
        return reply_out(chat_service().ask(user, body.message, conversation_id))
```

Replace it with:

```python
        return reply_out(chat_service().ask(user, body.message, conversation_id), user)
```

**Edit 11 of 14.** Find this text (it can be part of a line):

```python
        return reply_out(chat_service().ask(user, req.message, req.conversation_id))
```

Replace it with:

```python
        return reply_out(chat_service().ask(user, req.message, req.conversation_id), user)
```

**Edit 12 of 14.** Find this text (it can be part of a line):

```python
        return {"user": asdict(user), "business": asdict(repo.get_business(user.business_id))}
```

Replace it with:

```python
        return {"user": asdict(user), "business": asdict(repo.get_business(user.business_id)),
                "data_mode": data_mode(user)}

    @app.get("/api/reports/summary", tags=["reports"], dependencies=[only_params("period", "start", "end")])
    def report_summary(
        period: str | None = Query(None, description="Calendar month, YYYY-MM"),
        start: date | None = Query(None, description="Custom range start (inclusive)"),
        end: date | None = Query(None, description="Custom range end (inclusive)"),
        user: User = Depends(current_user),
    ) -> dict:
        """Invoices and bills ISSUED in a period, for the signed-in user's business only."""
        p = resolve_period(period, start, end, current_date(), settings.reporting_timezone, settings.max_period_days)
        business = repo.get_business(user.business_id)

        def block(items) -> dict:
            dated = [i for i in items if p.contains(i.issue_date)]
            return {
                "issued_count": len(dated),
                "issued_total": round(sum(i.amount for i in dated), 2),
                "paid_to_date": round(sum(i.amount_paid for i in dated), 2),
                "outstanding_now": round(sum(i.outstanding for i in dated), 2),
                "undated_excluded": sum(1 for i in items if i.issue_date is None),
            }

        return {
            "period": {"start": p.start, "end": p.end, "timezone": p.timezone},
            "data_mode": "demo" if business.is_demo else "actual",
            "currency": business.currency,
            "receivables": block(repo.list("receivables", business.id)),
            "payables": block(repo.list("payables", business.id)),
            "as_of": current_date(),
            "note": "Payments carry no date in this data model, so paid_to_date and outstanding_now are "
                    "as of today, not as of the period end.",
        }
```

**Edit 13 of 14.** Find this text (it can be part of a line):

```python
    @app.get("/api/demo-users", tags=["demo"])
    def demo_users() -> list[dict]:
        """Demo-only: powers the UI's user switcher. Remove in production."""
        users = []
```

Replace it with:

```python
    @app.get("/api/demo-users", tags=["demo"])
    def demo_users() -> list[dict]:
        """Powers the demo UI's user switcher. Exists only in dev auth mode."""
        if settings.auth_mode != "dev":
            raise HTTPException(404, "Not found")
        users = []
```

**Edit 14 of 14.** Find this text (it can be part of a line):

```python
    return create_app(repo, today=today)
```

Replace it with:

```python
    return create_app(repo, today=today)  # settings come from the environment
```

**Do this (2 of 4).** Edit `tests/conftest.py`. Your existing tests use the `X-User-Id` header, so they run in dev mode. Production behaviour is tested separately in Step 13:

**Edit 1 of 2.** Find this text (it can be part of a line):

```python
from datetime import date
```

Replace it with:

```python
import os
from datetime import date
```

**Edit 2 of 2.** Find this text (it can be part of a line):

```python
from app import create_app
```

Replace it with:

```python
# Tests run in dev auth mode with demo data visible. These must be set before the app is
# imported. Production-mode behaviour is tested explicitly in tests/test_security.py.
os.environ.update({"AUTH_MODE": "dev", "ALLOW_DEV_AUTH": "true", "APP_ENV": "test", "ALLOW_DEMO_DATA": "true"})

from app import create_app  # noqa: E402
```

**Do this (3 of 4).** Add two lines to the end of `requirements.txt`:

```
pyjwt>=2.8
tzdata>=2024.1
```

**Do this (4 of 4).** Create your local settings. Copy the example and keep the real `.env` out of Git:

```powershell
Copy-Item C:\Users\Comtech\HisabDO\implementation-guide\reference\.env.example C:\Users\Comtech\HisabDO\conversation-management\.env.example
```

The app reads environment variables, so for a local run set them in PowerShell:

```powershell
$env:AUTH_MODE = "dev"; $env:APP_ENV = "development"; $env:ALLOW_DEV_AUTH = "true"; $env:ALLOW_DEMO_DATA = "true"
```

**Check.** `pytest -q` prints `161 passed`. Then start the server with `uvicorn app:default_app --factory` and try these in a second terminal:

| Try | Expected |
|---|---|
| `GET /api/receivables` with no header | 401 |
| `GET /api/receivables` with `X-User-Id: U-001` | 200 |
| `GET /api/receivables?business_id=B-002` with the header | 400 |
| `GET /api/reports/summary?period=2026-09` with the header | Receivables issued: 3, total 203500 |
| `GET /api/me` with the header | `"data_mode": "demo"` |

## Step 13: Add the security and retrieval tests

**Why.** The deliverable asks for security test cases, and tests are also how you know the next change doesn't quietly undo this work.

**Do this.** Copy the test files and fixtures:

```powershell
Copy-Item -Recurse -Force C:\Users\Comtech\HisabDO\implementation-guide\reference\tests\* C:\Users\Comtech\HisabDO\conversation-management\tests\
```

| File | Tests | What it proves |
|---|---|---|
| `tests/test_security.py` | 45 | Nothing works without a login; 13 kinds of forged token are rejected; one business can't read, change or delete another's records; smuggled parameters are refused; unsafe settings refuse to start; demo data is labelled and gated |
| `tests/test_reports.py` | 18 | Period totals match a hand calculation; first and last days are included; months add up to the whole range; bad periods are rejected; "today" is the business's date |
| `tests/test_kb_retrieval.py` | 34 | A question finds its answer with zero shared words; off-topic questions retrieve nothing; drafts are never indexed; outages degrade safely; cited sources are reported and uncited or unretrieved ones are stripped; versions switch and roll back; note vectors never cross businesses |
| `tests/kb_helpers.py` | (helper) | A fake embedder that maps English and Roman Urdu words to shared concepts, so the tests need no API key |
| `tests/fixtures/` | (data) | Two small KB versions used only by the tests |

**Check.** `pytest -q` prints `258 passed`.

---

# Going live

## Step 14: Fill, index and tune the knowledge base

**Why.** Until this step the knowledge base is empty on purpose: every shipped entry is a draft, so the chatbot answers product questions with "I don't have verified information". That is the correct behaviour for an unverified KB.

**0. Copy the two scripts** this step uses:

```powershell
Copy-Item -Recurse -Force C:\Users\Comtech\HisabDO\implementation-guide\reference\scripts C:\Users\Comtech\HisabDO\conversation-management\scripts
```

**1. Get content verified.** For each entry in `kb/v1/faqs.json` and `kb/v1/docs/`:

- Replace the draft text with the real answer from the product team.
- Set `"status": "verified"`, `"verified_by"` (a person or team) and `"verified_on"` (a date like `2026-10-14`).
- Fill in `"source"`, so the user can be told where the answer comes from.
- Add new entries with the next free ID. Never reuse an ID for a different topic.
- Put the release date in `manifest.json` and describe the change in `kb/CHANGELOG.md`.

**2. Set your Gemini key** (in PowerShell, never in a file you commit):

```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

**3. Build the index.** This validates the files, embeds the verified entries, and stores them without making them live:

```powershell
python scripts/build_kb_index.py kb/v1
```

**4. Make it live:**

```powershell
python scripts/build_kb_index.py kb/v1 --activate
```

**5. Tune the threshold.** The default `0.60` is a starting guess, not a measured value. Edit `kb/eval_questions.json` so it lists real questions and the entry each should find (`null` for questions the KB must not answer), then run:

```powershell
python scripts/calibrate_threshold.py kb/eval_questions.json
```

It prints every question's score and suggests a threshold. Read the result this way:

- **False answers** (it answered something it should have refused) are the dangerous kind. Raise the threshold until there are none.
- **Missed** (it had the answer but said "I don't know") is the cost of a high threshold. Lower it if there are many and no false answers appear.

Set the chosen value with `$env:KB_THRESHOLD = "0.65"` (or in your deployment settings) and restart.

**6. Releasing a new version later.** Copy `kb/v1` to `kb/v2`, change the content, raise `kb_version` in the manifest, then index and activate it. To go back:

```powershell
python scripts/build_kb_index.py --list
```

```powershell
python scripts/build_kb_index.py --activate-version 1.0.0
```

## Step 15: Switch on real logins

**Do this when the auth team is ready.** On the server, set:

| Variable | Value |
|---|---|
| `AUTH_MODE` | `supabase` |
| `APP_ENV` | `production` |
| `SUPABASE_JWT_SECRET` | The project's JWT secret, from the Supabase dashboard. Server-side only. |
| `ALLOW_DEMO_DATA` | `false` |
| `ALLOW_DEV_AUTH` | leave unset |

Then link each real user to their login by storing the Supabase user ID in `users.auth_id`. Until a user is linked, a valid login gets 401 with "This account has no access to HisabDo data".

Mark real businesses with `is_demo = 0`. They are then labelled `actual` and are not blocked.

---

# What this does not solve yet

| Limit | What to do about it |
|---|---|
| **Payments have no dates.** A receivable stores only how much has been paid, not when. So a report can say what was invoiced in September, but "paid" and "outstanding" are as of today. The report says this in its `note` field. | Add a payments table with a date per payment. |
| **Data is in SQLite.** The team's rule is one shared Supabase PostgreSQL database, with row-level security. | Port the repository to Supabase, and move vectors to `pgvector`. `VectorStore` and `Repository` are the only classes that change. |
| **No rate limiting.** Repeated bad logins are not slowed down. | Add it at the API gateway. |
| **The chat page doesn't show sources yet.** The API returns `sources`, `knowledge_base` and `data_mode`, but `static/index.html` doesn't display them. | Show each source's title and KB version under the answer. |
| **Free-tier privacy.** Google may use free-tier prompts and embedding inputs to improve its products. | Use a paid key before real customer notes are embedded. |
| **Customer names still use exact matching.** That is deliberate: names and record IDs are precise values, and exact matching is more reliable for them than "similar meaning". | No change needed. |

# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Server won't start: "AUTH_MODE=dev is refused" | Dev mode needs `ALLOW_DEV_AUTH=true` and a non-production `APP_ENV` | Set both variables (Step 12) |
| Every request returns 401 | `AUTH_MODE` is not set, so authentication is disabled | Set `AUTH_MODE` to `dev` locally or `supabase` in production |
| 403 "Demo data is disabled" | The business is flagged demo and `ALLOW_DEMO_DATA` is off | Turn it on locally; in production, use real businesses |
| `/api/me` says `actual` for seed data | Your old `data/app.db` was created before the seed change | Delete `data/app.db` and restart (Step 2) |
| Chat says product information is unavailable | No `GEMINI_API_KEY`, or the index was built with a different embedding model | Set the key; rebuild the index with the current model |
| Chat says it has no verified information for a question the KB covers | The score is below the threshold, or the entry is still a draft | Run the calibration script; check the entry's `status` |
| `build_kb_index.py` says "nothing to index" | No entry is verified yet | Complete Step 14, part 1 |
| `ModuleNotFoundError: jwt` or timezone errors on Windows | Missing libraries | `pip install pyjwt tzdata` |
