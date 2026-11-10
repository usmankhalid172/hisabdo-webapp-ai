"""Fetch the signed-in user's business data from the database, pick what's
relevant to the question, and render it as structured, citable context.

Design points:

* **Relevance, not dump.** Only records that match the question (by name,
  company, vendor, ID, intent keywords, or the conversation's current focus)
  are included, so the model isn't distracted and the prompt stays small.
* **Every record has an ID** the model must cite; the set of included IDs is
  returned so the grounding validator can reject citations to anything that
  wasn't actually shown to the model.
* **Money is precomputed.** Each customer carries its outstanding and overdue
  balance, and ``<summary_stats>`` carries business-wide totals, so "How much
  does Ahmed owe?" is answered by quoting a number, not by model arithmetic.
* **Coverage is explicit.** ``<retrieval_scope>`` says how many records exist
  vs. were loaded, so the model can say "not in the data I was given" instead
  of wrongly asserting something doesn't exist.
* **All values are XML-escaped**, so free text in notes can't close a tag and
  masquerade as instructions or as another record.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable
from xml.sax.saxutils import escape, quoteattr

from .models import Business, Customer, Note, Payable, Receivable, Task, User
from .repository import Repository
from .retrieval import RetrievalResult

MAX_CUSTOMERS = 30
MAX_TASKS = 25
MAX_NOTES_PER_CUSTOMER = 10
MAX_KEYWORD_NOTES = 5
MAX_NOTE_CHARS = 1200
MAX_RECEIVABLES = 30
MAX_PAYABLES = 30

_STOPWORDS = frozenset(
    """a an and are about any at be by can could did do does for from get give
    has have how i in is it its me my of on or our please show should tell than
    that the their them they this to was we what when where which who why will
    with would you your all there much many latest last recent us owe owes owed
    customer customers client clients task tasks note notes business today week
    invoice invoices bill bills payment payments balance due""".split()
)

_CUSTOMER_LIST = re.compile(r"\b(customers|clients|leads?|accounts|churn(ed)?|pipeline)\b")
_TASK_INTENT = re.compile(
    r"\b(tasks?|to-?dos?|overdue|deadlines?|follow[- ]?ups?|assigned|priorit\w*|"
    r"focus|plan|today|this week|pending|open items?)\b"
)
_NOTE_INTENT = re.compile(r"\b(notes?|said|mentioned|discuss\w*|meetings?|calls?|history|feedback)\b")
_MONEY_INTENT = re.compile(
    r"\b(owe[sd]?|owing|balances?|invoices?|receivables?|payables?|bills?|pay(ments?)?|paid|"
    r"outstanding|dues?|credit|debt|cash|collect\w*|recover\w*|udhaar|baqaya|money|amount)\b"
)
_PAYABLE_INTENT = re.compile(
    r"\b((we|i)\s+(owe|have to pay|need to pay|must pay)|payables?|bills?|suppliers?|vendors?|creditors?)\b"
)
_RECEIVABLE_INTENT = re.compile(
    r"\b(owes? (us|me)|receivables?|invoices?|collect\w*|recover\w*|debtors?|who owes|customers? owe)\b"
)
_RECORD_ID = re.compile(r"\b([UBCTNRP]-\d{3,})\b", re.IGNORECASE)


@dataclass
class ContextBundle:
    """The rendered context plus metadata about what went into it."""

    text: str
    source_ids: set[str]
    focus_customer_ids: list[str]
    included: dict[str, list[str]] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)
    kb_ids: list[str] = field(default_factory=list)  # knowledge-base entries shown to the model


class ContextBuilder:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def build(
        self,
        user_id: str,
        question: str,
        today: date,
        focus_customer_ids: list[str] | None = None,
        kb: RetrievalResult | None = None,
        note_ranker: Callable[[list[Note]], list[Note] | None] | None = None,
    ) -> ContextBundle:
        # 1. Fetch: everything below is scoped to the signed-in user's business.
        user = self.repo.get_user(user_id)
        business = self.repo.get_business(user.business_id)
        team: list[User] = self.repo.list("users", business.id)
        customers: list[Customer] = self.repo.list("customers", business.id)
        tasks: list[Task] = self.repo.list("tasks", business.id)
        notes: list[Note] = self.repo.list("notes", business.id)
        receivables: list[Receivable] = self.repo.list("receivables", business.id)
        payables: list[Payable] = self.repo.list("payables", business.id)

        q = question.lower()
        terms = _keywords(q)
        money_q = bool(_MONEY_INTENT.search(q))

        # 2. Select. --- Customers ------------------------------------------------
        matched = [c for c in customers if _customer_mentioned(c, q, terms)]
        if not matched and focus_customer_ids and not _PAYABLE_INTENT.search(q):
            # Follow-up like "what about their open tasks?" -> keep prior focus.
            focus = set(focus_customer_ids)
            matched = [c for c in customers if c.id in focus]
        matched_ids = {c.id for c in matched}

        listed: list[Customer] = list(matched)
        if _CUSTOMER_LIST.search(q):
            status = next((s for s in ("lead", "active", "churned") if s in q), None)
            pool = [c for c in customers if status is None or c.status == status]
            listed += sorted((c for c in pool if c.id not in matched_ids), key=lambda c: c.name)

        # --- Receivables (money customers owe us) ------------------------------------
        chosen_recv = [r for r in receivables if r.customer_id in matched_ids]
        if money_q and not matched and (_RECEIVABLE_INTENT.search(q) or not _PAYABLE_INTENT.search(q)):
            chosen_recv += [r for r in receivables if r.outstanding > 0]
        chosen_recv = _dedupe(sorted(chosen_recv, key=lambda r: _balance_urgency(r, today)))[:MAX_RECEIVABLES]

        # --- Payables (money we owe vendors) --------------------------------------------
        vendor_hits = [p for p in payables if _keywords(p.vendor_name.lower()) & terms]
        chosen_pay = list(vendor_hits)
        if money_q and not vendor_hits and not matched and (
            _PAYABLE_INTENT.search(q) or not _RECEIVABLE_INTENT.search(q)
        ):
            chosen_pay += [p for p in payables if p.outstanding > 0]
        chosen_pay = _dedupe(sorted(chosen_pay, key=lambda p: _balance_urgency(p, today)))[:MAX_PAYABLES]

        # --- Tasks ---------------------------------------------------------------------
        chosen_tasks: list[Task] = [t for t in tasks if t.customer_id in matched_ids]
        if _TASK_INTENT.search(q) and not (money_q and "overdue" in q and not re.search(r"\btasks?\b", q)):
            pool = [t for t in tasks if t.is_open()]
            if re.search(r"\b(my|me|i)\b", q):
                pool = [t for t in pool if t.assignee_id == user.id]
            if "overdue" in q:
                pool = [t for t in pool if t.is_overdue(today)]
            elif "today" in q:
                pool = [t for t in pool if t.due_date is not None and t.due_date <= today]
            elif "this week" in q:
                horizon = today + timedelta(days=7)
                pool = [t for t in pool if t.due_date is not None and t.due_date <= horizon]
            chosen_tasks += pool
        chosen_tasks = _dedupe(sorted(chosen_tasks, key=lambda t: _task_urgency(t, today)))[:MAX_TASKS]

        # --- Notes ---------------------------------------------------------------------
        chosen_notes: list[Note] = []
        for c in matched:
            own = sorted((n for n in notes if n.customer_id == c.id), key=lambda n: n.created_at, reverse=True)
            chosen_notes += own[:MAX_NOTES_PER_CUSTOMER]
        semantic = note_ranker(notes) if note_ranker else None
        if semantic is not None:
            # Semantic search: ranked by meaning, so "udhaar limit" finds a note about "credit limit".
            chosen_notes += semantic
        elif terms and (_NOTE_INTENT.search(q) or not matched):
            # Fallback only (embeddings unavailable): keyword overlap.
            scored = [(len(terms & _keywords(n.content.lower())), n) for n in notes]
            scored = [(s, n) for s, n in scored if s > 0]
            scored.sort(key=lambda sn: (-sn[0], -sn[1].created_at.timestamp()))
            chosen_notes += [n for _, n in scored[:MAX_KEYWORD_NOTES]]
        chosen_notes = _dedupe(chosen_notes)

        # Any customer referenced by an included record must be resolvable by name.
        referenced = (
            {t.customer_id for t in chosen_tasks}
            | {n.customer_id for n in chosen_notes}
            | {r.customer_id for r in chosen_recv}
        )
        listed_ids = {c.id for c in listed}
        listed += [c for c in customers if c.id in referenced - listed_ids]
        listed = listed[:MAX_CUSTOMERS]

        # 3. Render.
        balances = _customer_balances(receivables, today)
        user_names = {u.id: u.name for u in team}
        customer_names = {c.id: c.name for c in customers}
        cur = business.currency
        sections = [
            _render_user(user),
            _render_business(business),
            _render_team(team),
            _render_summary(business, customers, tasks, notes, receivables, payables, today),
            _render_customers(listed, balances, cur),
            _render_receivables(chosen_recv, today, customer_names, cur),
            _render_payables(chosen_pay, today, cur),
            _render_tasks(chosen_tasks, today, user_names, customer_names),
            _render_notes(chosen_notes, user_names, customer_names),
            _render_kb(kb),
            _render_scope(
                customers=(len(listed), len(customers)),
                receivables=(len(chosen_recv), len(receivables)),
                payables=(len(chosen_pay), len(payables)),
                tasks=(len(chosen_tasks), len(tasks)),
                notes=(len(chosen_notes), len(notes)),
            ),
        ]
        text = f'<business_context as_of="{today.isoformat()}">\n' + "\n".join(s for s in sections if s) + "\n</business_context>"

        kb_ids = {s.id for s in kb.sources} if kb is not None and kb.status == "ok" else set()
        source_ids = (
            {user.id, business.id}
            | {u.id for u in team}
            | {c.id for c in listed}
            | {r.id for r in chosen_recv}
            | {p.id for p in chosen_pay}
            | {t.id for t in chosen_tasks}
            | {n.id for n in chosen_notes}
            | kb_ids
        )
        return ContextBundle(
            text=text,
            source_ids=source_ids,
            focus_customer_ids=[c.id for c in matched],
            included={
                "customers": [c.id for c in listed],
                "receivables": [r.id for r in chosen_recv],
                "payables": [p.id for p in chosen_pay],
                "tasks": [t.id for t in chosen_tasks],
                "notes": [n.id for n in chosen_notes],
            },
            kb_ids=sorted(kb_ids),
            totals={
                "customers": len(customers),
                "receivables": len(receivables),
                "payables": len(payables),
                "tasks": len(tasks),
                "notes": len(notes),
            },
        )


# --- matching helpers ------------------------------------------------------------


def _keywords(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9'-]+", text) if len(w) >= 3 and w not in _STOPWORDS}


def _customer_mentioned(c: Customer, q: str, terms: set[str]) -> bool:
    if c.id.lower() in {m.lower() for m in _RECORD_ID.findall(q)}:
        return True
    if c.name.lower() in q or (c.company and c.company.lower() in q) or (c.email and c.email.lower() in q):
        return True
    # Single distinctive name/company token, e.g. "Ahmed" or "Madina".
    tokens = _keywords(c.name.lower()) | _keywords(c.company.lower())
    return bool(tokens & terms)


def _task_urgency(t: Task, today: date) -> tuple:
    prio = {"high": 0, "medium": 1, "low": 2}.get(t.priority, 3)
    return (not t.is_overdue(today), not t.is_open(), prio, t.due_date or date.max, t.id)


def _balance_urgency(b: Receivable | Payable, today: date) -> tuple:
    order = {"overdue": 0, "partially_paid": 1, "unpaid": 1, "paid": 2}[b.state(today)]
    return (order, b.due_date or date.max, b.id)


def _customer_balances(receivables: list[Receivable], today: date) -> dict[str, tuple[float, float]]:
    out: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in receivables:
        out[r.customer_id][0] += r.outstanding
        if r.state(today) == "overdue":
            out[r.customer_id][1] += r.outstanding
    return {k: (round(v[0], 2), round(v[1], 2)) for k, v in out.items()}


def _dedupe(items: list) -> list:
    seen: set[str] = set()
    out = []
    for item in items:
        if item.id not in seen:
            seen.add(item.id)
            out.append(item)
    return out


# --- rendering ---------------------------------------------------------------------


def _attrs(**values: object) -> str:
    return " ".join(f"{k}={quoteattr(str(v))}" for k, v in values.items() if v not in (None, "", []))


def _money(value: float) -> str:
    return f"{value:.2f}"


def _render_user(u: User) -> str:
    return f"<current_user {_attrs(id=u.id, name=u.name, role=u.role, email=u.email, timezone=u.timezone)}/>"


def _render_business(b: Business) -> str:
    mode = "demo" if b.is_demo else "actual"
    lines = [f"<business {_attrs(id=b.id, name=b.name, industry=b.industry, currency=b.currency, data_mode=mode)}>"]
    if b.description:
        lines.append(f"  <description>{escape(b.description)}</description>")
    if b.services:
        lines.append(f"  <services>{escape('; '.join(b.services))}</services>")
    if b.hours:
        lines.append(f"  <hours>{escape(b.hours)}</hours>")
    for name, text in b.policies.items():
        lines.append(f"  <policy {_attrs(name=name)}>{escape(text)}</policy>")
    lines.append("</business>")
    return "\n".join(lines)


def _render_team(team: list[User]) -> str:
    rows = [f"  <member {_attrs(id=u.id, name=u.name, role=u.role)}/>" for u in team]
    return "<team>\n" + "\n".join(rows) + "\n</team>"


def _render_summary(
    b: Business,
    customers: list[Customer],
    tasks: list[Task],
    notes: list[Note],
    receivables: list[Receivable],
    payables: list[Payable],
    today: date,
) -> str:
    by_status = {s: sum(1 for c in customers if c.status == s) for s in ("lead", "active", "churned")}
    open_tasks = [t for t in tasks if t.is_open()]
    overdue_tasks = [t for t in open_tasks if t.is_overdue(today)]
    week = today + timedelta(days=7)

    def money_attrs(items: list[Receivable] | list[Payable]) -> str:
        open_items = [i for i in items if i.outstanding > 0]
        overdue = [i for i in open_items if i.state(today) == "overdue"]
        due_soon = [i for i in open_items if i.due_date and today <= i.due_date <= week]
        return (
            f'open_count="{len(open_items)}" outstanding_total="{_money(sum(i.outstanding for i in open_items))}" '
            f'overdue_count="{len(overdue)}" overdue_total="{_money(sum(i.outstanding for i in overdue))}" '
            f'due_next_7_days_total="{_money(sum(i.outstanding for i in due_soon))}"'
        )

    return (
        '<summary_stats note="Precomputed over ALL records for this business; quote these rather than recounting.">\n'
        f'  <customers total="{len(customers)}" lead="{by_status["lead"]}" active="{by_status["active"]}" '
        f'churned="{by_status["churned"]}"/>\n'
        f"  <receivables currency={quoteattr(b.currency)} {money_attrs(receivables)} "
        'meaning="money customers owe the business"/>\n'
        f"  <payables currency={quoteattr(b.currency)} {money_attrs(payables)} "
        'meaning="money the business owes vendors"/>\n'
        f'  <tasks total="{len(tasks)}" open="{len(open_tasks)}" overdue="{len(overdue_tasks)}" '
        f'high_priority_open="{sum(1 for t in open_tasks if t.priority == "high")}"/>\n'
        f'  <notes total="{len(notes)}"/>\n'
        "</summary_stats>"
    )


def _render_customers(customers: list[Customer], balances: dict, currency: str) -> str:
    if not customers:
        return "<customers/>"
    rows = []
    for c in customers:
        outstanding, overdue = balances.get(c.id, (0.0, 0.0))
        rows.append(
            "  <customer "
            + _attrs(
                id=c.id,
                name=c.name,
                company=c.company,
                status=c.status,
                email=c.email,
                phone=c.phone,
                outstanding_balance=_money(outstanding),
                overdue_balance=_money(overdue),
                currency=currency,
                last_contact=c.last_contact.isoformat() if c.last_contact else None,
                tags=", ".join(c.tags),
            )
            + "/>"
        )
    return "<customers>\n" + "\n".join(rows) + "\n</customers>"


def _render_receivables(items: list[Receivable], today: date, customers: dict[str, str], currency: str) -> str:
    if not items:
        return "<receivables/>"
    rows = []
    for r in items:
        attrs = _attrs(
            id=r.id,
            customer=f"{customers.get(r.customer_id, 'unknown')} ({r.customer_id})",
            invoice=r.invoice_number,
            amount=_money(r.amount),
            paid=_money(r.amount_paid),
            outstanding=_money(r.outstanding),
            currency=currency,
            issued=r.issue_date.isoformat() if r.issue_date else None,
            due=r.due_date.isoformat() if r.due_date else None,
            state=r.state(today),
        )
        rows.append(f"  <receivable {attrs}>{escape(r.description)}</receivable>")
    return "<receivables>\n" + "\n".join(rows) + "\n</receivables>"


def _render_payables(items: list[Payable], today: date, currency: str) -> str:
    if not items:
        return "<payables/>"
    rows = []
    for p in items:
        attrs = _attrs(
            id=p.id,
            vendor=p.vendor_name,
            bill=p.bill_number,
            amount=_money(p.amount),
            paid=_money(p.amount_paid),
            outstanding=_money(p.outstanding),
            currency=currency,
            issued=p.issue_date.isoformat() if p.issue_date else None,
            due=p.due_date.isoformat() if p.due_date else None,
            state=p.state(today),
        )
        rows.append(f"  <payable {attrs}>{escape(p.description)}</payable>")
    return "<payables>\n" + "\n".join(rows) + "\n</payables>"


def _render_tasks(tasks: list[Task], today: date, users: dict[str, str], customers: dict[str, str]) -> str:
    if not tasks:
        return "<tasks/>"
    rows = []
    for t in tasks:
        attrs = _attrs(
            id=t.id,
            status=t.status,
            priority=t.priority,
            due=t.due_date.isoformat() if t.due_date else None,
            overdue="yes" if t.is_overdue(today) else None,
            assignee=f"{users.get(t.assignee_id, 'unknown')} ({t.assignee_id})" if t.assignee_id else "unassigned",
            customer=f"{customers.get(t.customer_id, 'unknown')} ({t.customer_id})" if t.customer_id else None,
        )
        body = escape(t.title) + (f" - {escape(t.description)}" if t.description else "")
        rows.append(f"  <task {attrs}>{body}</task>")
    return "<tasks>\n" + "\n".join(rows) + "\n</tasks>"


def _render_notes(notes: list[Note], users: dict[str, str], customers: dict[str, str]) -> str:
    if not notes:
        return "<notes/>"
    rows = []
    for n in notes:
        content = n.content if len(n.content) <= MAX_NOTE_CHARS else n.content[:MAX_NOTE_CHARS] + " ...[truncated]"
        attrs = _attrs(
            id=n.id,
            created=n.created_at.isoformat(timespec="minutes"),
            author=f"{users.get(n.author_id, 'unknown')} ({n.author_id})",
            customer=f"{customers.get(n.customer_id, 'unknown')} ({n.customer_id})" if n.customer_id else None,
        )
        rows.append(f"  <note {attrs}>{escape(content)}</note>")
    return '<notes untrusted_content="true">\n' + "\n".join(rows) + "\n</notes>"


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
    rows = [f'  <{kind} loaded="{shown}" exist="{total}"/>' for kind, (shown, total) in counts.items()]
    return (
        '<retrieval_scope note="Only records relevant to this question were loaded. '
        'A record missing here may still exist in the system.">\n' + "\n".join(rows) + "\n</retrieval_scope>"
    )
