"""
account_data.py - the PRIVATE route: a user's own numbers (balance, reports).

Rules (Day 15 §6.1, same boundary as financial_assistant/service.py):
  - Exact user figures come ONLY from the authenticated backend financial API
    (src/integration/backend_client.py). Never from the FAQ knowledge base,
    never from the LLM.
  - Only the user_id of the current request is sent (the third-party guard in
    service.py already refused questions about anyone else).
  - Replies are fixed templates, so the numbers shown are exactly the numbers
    the backend returned.

BackendClientAccountData adapts the team's existing BackendClient
(get_user_financial_summary). Today that client is the MOCK client, so every
answer is labelled "demo data" until the real backend contract lands.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from .models import Period


class AccountDataNotConnected(Exception):
    """No data source is configured for private account questions."""


class AccountDataError(Exception):
    """The data source failed (timeout, 5xx ...). Details stay in the server logs."""


class PeriodNotAvailable(Exception):
    """The backend cannot give figures for the requested period yet."""


class AccountRef(BaseModel):
    id: str
    name: str
    data_mode: str = "actual"   # "demo" accounts/data are labelled in every answer


class AccountSummary(BaseModel):
    account: AccountRef
    currency: str
    period: Period
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    closing_balance: Decimal
    transaction_count: int | None = None
    outstanding_receivables: Decimal | None = None
    top_expense_category: str | None = None
    top_expense_amount: Decimal | None = None


class AccountDataProvider(ABC):
    name = "base"

    @abstractmethod
    def list_accounts(self, user_id: str) -> list[AccountRef]: ...

    @abstractmethod
    def summary(self, user_id: str, account_id: str, period: Period) -> AccountSummary: ...


class NotConnectedAccountData(AccountDataProvider):
    name = "none"

    def list_accounts(self, user_id: str) -> list[AccountRef]:
        raise AccountDataNotConnected()

    def summary(self, user_id: str, account_id: str, period: Period) -> AccountSummary:
        raise AccountDataNotConnected()


class BackendClientAccountData(AccountDataProvider):
    """
    Uses the existing BackendClient seam. Its contract today only has
    "this month" totals and the current balance, so other periods are
    answered honestly with "not available yet" instead of being estimated.
    """

    name = "backend_client"

    def __init__(self, client=None, today=date.today):
        if client is None:
            from ...integration.backend_client import get_backend_client
            client = get_backend_client()
        self.client = client
        self.today = today

    def list_accounts(self, user_id: str) -> list[AccountRef]:
        return [AccountRef(id="primary", name="Your account", data_mode=self._mode(None))]

    def summary(self, user_id: str, account_id: str, period: Period) -> AccountSummary:
        today = self.today()
        if not (period.start.year == today.year and period.start.month == today.month):
            raise PeriodNotAvailable()
        try:
            data = self.client.get_user_financial_summary(user_id)
        except Exception as exc:  # noqa: BLE001 - any backend failure -> one safe error
            raise AccountDataError(type(exc).__name__) from exc
        income = Decimal(str(data["total_revenue_this_month"]))
        expense = Decimal(str(data["total_expenses_this_month"]))
        return AccountSummary(
            account=AccountRef(id=account_id, name="Your account", data_mode=self._mode(data)),
            currency=data.get("currency", "PKR"), period=period,
            total_income=income, total_expense=expense, net=income - expense,
            closing_balance=Decimal(str(data["balance"])),
            outstanding_receivables=Decimal(str(data["outstanding_receivables"]))
            if data.get("outstanding_receivables") is not None else None,
        )

    def _mode(self, data: dict | None) -> str:
        source = str((data or {}).get("source", "")) if data else type(self.client).__name__
        return "demo" if "MOCK" in source.upper() else "actual"


class FakeAccountData(AccountDataProvider):
    """TESTS ONLY: fixed synthetic numbers per user. No real data."""

    name = "fake"

    def __init__(self, accounts: dict[str, list[AccountRef]] | None = None, fail: bool = False):
        self.accounts = accounts or {}
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def list_accounts(self, user_id: str) -> list[AccountRef]:
        self.calls.append(("list", user_id))
        if self.fail:
            raise AccountDataError("boom")
        return self.accounts.get(user_id, [])

    def summary(self, user_id: str, account_id: str, period: Period) -> AccountSummary:
        self.calls.append(("summary", user_id))
        if self.fail:
            raise AccountDataError("boom")
        acct = next(a for a in self.accounts.get(user_id, []) if a.id == account_id)
        return AccountSummary(account=acct, currency="PKR", period=period, total_income=Decimal("150000"),
                              total_expense=Decimal("16500.80"), net=Decimal("133499.20"), transaction_count=5,
                              closing_balance=Decimal("153499.20"), top_expense_category="Transport",
                              top_expense_amount=Decimal("4000"))


def create_account_data_provider(name: str = "backend_client") -> AccountDataProvider:
    if name in ("", "backend_client"):
        return BackendClientAccountData()
    if name == "none":
        return NotConnectedAccountData()
    raise ValueError(f"Unknown account data provider '{name}'")


def today_period(today: date) -> Period:
    first = today.replace(day=1)
    return Period(start=first, end=today, label="this month so far")
