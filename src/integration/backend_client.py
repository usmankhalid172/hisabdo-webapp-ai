"""Client for the application's financial data API."""
from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date


class BackendClient(ABC):
    @abstractmethod
    def get_user_financial_summary(self, user_id: str) -> dict:
        ...


class MockBackendClient(BackendClient):
    """Demo figures only; not actual customer financial data."""

    def get_user_financial_summary(self, user_id: str) -> dict:
        today = date.today()
        period_start = today.replace(day=1)
        period_end = today.replace(
            day=monthrange(today.year, today.month)[1]
        )

        return {
            "user_id": user_id,
            "balance": 45230.50,
            "currency": "PKR",
            "total_expenses_this_month": 18420.00,
            "total_revenue_this_month": 62000.00,
            "outstanding_receivables": 9000.00,
            "reporting_period": "Current calendar month (demo)",
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "data_type": "DEMO",
            "is_mock_data": True,
            "source": (
                "MockBackendClient - demo figures only; "
                "not actual customer data."
            ),
        }


def get_backend_client() -> BackendClient:
    return MockBackendClient()