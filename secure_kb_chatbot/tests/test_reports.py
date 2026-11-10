"""Reporting-period accuracy: periods are local calendar days and totals are exact."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from chatbot.periods import InvalidPeriod, local_today, resolve_period
from conftest import EMPTY_TENANT, OTHER_TENANT, OWNER

URL = "/api/reports/summary"


def report(client, query="", headers=OWNER):
    r = client.get(URL + query, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_september_matches_a_hand_calculation(client):
    r = report(client, "?period=2026-09")
    assert r["period"] == {"start": "2026-09-01", "end": "2026-09-30", "timezone": "Asia/Karachi"}
    # Invoices issued in September: R-005 (1 Sep) 18,500 + R-004 (10 Sep) 120,000 + R-002 (25 Sep) 65,000
    assert r["receivables"] == {"issued_count": 3, "issued_total": 203500.0, "paid_to_date": 38500.0,
                                "outstanding_now": 165000.0, "undated_excluded": 0}
    # Bills dated September: P-001 (5 Sep) 250,000 + P-002 (28 Sep) 48,000
    assert r["payables"] == {"issued_count": 2, "issued_total": 298000.0, "paid_to_date": 100000.0,
                             "outstanding_now": 198000.0, "undated_excluded": 0}
    assert r["currency"] == "PKR" and r["as_of"] == "2026-10-07"


def test_first_and_last_day_of_the_period_are_included(client):
    assert report(client, "?start=2026-09-01&end=2026-09-01")["receivables"]["issued_count"] == 1  # R-005
    assert report(client, "?start=2026-09-25&end=2026-09-25")["receivables"]["issued_count"] == 1  # R-002
    assert report(client, "?start=2026-09-02&end=2026-09-09")["receivables"]["issued_count"] == 0


def test_months_add_up_to_the_whole_range(client):
    months = [report(client, f"?period=2026-{m:02d}") for m in range(5, 11)]
    whole = report(client, "?start=2026-05-01&end=2026-10-31")
    for side in ("receivables", "payables"):
        for key in ("issued_count", "issued_total", "paid_to_date", "outstanding_now"):
            assert round(sum(m[side][key] for m in months), 2) == whole[side][key], (side, key)
    assert whole["receivables"]["issued_count"] == 6  # every seed invoice counted exactly once


def test_default_period_is_the_current_month_in_the_reporting_timezone(client):
    assert report(client)["period"] == {"start": "2026-10-01", "end": "2026-10-31", "timezone": "Asia/Karachi"}


def test_records_without_a_date_are_excluded_and_counted(client):
    client.post("/api/receivables", json={"customer_id": "C-005", "amount": 5000}, headers=OWNER)
    r = report(client, "?period=2026-09")["receivables"]
    assert r["issued_total"] == 203500.0 and r["undated_excluded"] == 1  # not silently added to a month


def test_report_is_scoped_to_the_callers_business(client):
    other = report(client, "?period=2026-09", OTHER_TENANT)
    assert other["currency"] == "GBP" and other["receivables"]["issued_total"] == 900.0
    empty = report(client, "?period=2026-09", EMPTY_TENANT)
    assert empty["receivables"]["issued_count"] == 0 and empty["payables"]["issued_total"] == 0


@pytest.mark.parametrize(
    "query",
    ["?period=2026-13", "?period=2026-9", "?period=26-09", "?period=2026-09&start=2026-09-01&end=2026-09-02",
     "?start=2026-09-10", "?start=2026-09-10&end=2026-09-01", "?start=2025-01-01&end=2026-12-31",
     "?start=2026-02-30&end=2026-03-01", "?period=1999-01"],
)
def test_invalid_periods_are_rejected(client, query):
    assert client.get(URL + query, headers=OWNER).status_code == 422


def test_leap_year_and_month_lengths():
    today = date(2026, 10, 7)
    assert resolve_period("2028-02", None, None, today, "Asia/Karachi").end == date(2028, 2, 29)
    assert resolve_period("2026-02", None, None, today, "Asia/Karachi").end == date(2026, 2, 28)
    assert resolve_period(None, date(2026, 1, 1), date(2027, 1, 1), today, "Asia/Karachi", 366).start == date(2026, 1, 1)
    with pytest.raises(InvalidPeriod):
        resolve_period(None, date(2026, 1, 1), date(2027, 1, 2), today, "Asia/Karachi", 366)  # 367 days


def test_today_is_the_business_date_not_the_server_date():
    assert local_today("Asia/Karachi") == datetime.now(ZoneInfo("Asia/Karachi")).date()
    with pytest.raises(InvalidPeriod):
        local_today("Mars/Olympus")


def test_overdue_uses_the_business_date(repo, monkeypatch):
    """At 01:00 on 8 Oct in Karachi it is still 7 Oct in UTC: a task due 7 Oct is already overdue there."""
    import chatbot.service as service_module
    from chatbot import ChatService, ContextBuilder
    from chatbot.conversations import ConversationStore
    from conftest import FakeLLM

    monkeypatch.setattr(service_module, "local_today", lambda tz: date(2026, 10, 8) if tz == "Asia/Karachi" else date(2026, 10, 7))
    llm = FakeLLM()
    svc = ChatService(ContextBuilder(repo), llm, ConversationStore(repo), timezone="Asia/Karachi")
    svc.ask(repo.get_user("U-001"), "Which tasks are overdue?")
    context = llm.calls[0]["system"][1]["text"]
    assert 'as_of="2026-10-08"' in context and 'id="T-005"' not in context
    assert "T-002" not in context  # due 8 Oct: due today, not overdue
