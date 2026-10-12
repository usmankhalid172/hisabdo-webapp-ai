from calendar import monthrange
from datetime import date

from src.integration.backend_client import get_backend_client


def test_mock_data_is_explicitly_labelled():
    summary = get_backend_client().get_user_financial_summary("user-1")

    assert summary["data_type"] == "DEMO"
    assert summary["is_mock_data"] is True
    assert "not actual customer data" in summary["source"]


def test_reporting_period_matches_current_calendar_month():
    summary = get_backend_client().get_user_financial_summary("user-1")

    today = date.today()
    expected_start = today.replace(day=1)
    expected_end = today.replace(
        day=monthrange(today.year, today.month)[1]
    )

    assert summary["period_start"] == expected_start.isoformat()
    assert summary["period_end"] == expected_end.isoformat()


def test_mock_summary_preserves_requested_user_id():
    summary = get_backend_client().get_user_financial_summary("user-123")

    assert summary["user_id"] == "user-123"