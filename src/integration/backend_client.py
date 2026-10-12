
"""
Financial backend client.

Real financial data must not be fabricated while the backend
data contract is unavailable.
"""
from abc import ABC, abstractmethod

from ..errors import ServiceError


class BackendClient(ABC):
    @abstractmethod
    def get_user_financial_summary(self, user_id: str) -> dict:
        ...


class MockBackendClient(BackendClient):
    """Fail safely instead of returning fake financial figures."""

    def get_user_financial_summary(self, user_id: str) -> dict:
        raise ServiceError(
            "FINANCIAL_BACKEND_UNAVAILABLE",
            "Actual account-specific financial data is not available yet.",
            status_code=503,
        )


def get_backend_client() -> BackendClient:
    # Replace this with the real authenticated backend client
    # after the financial data contract is finalized.
    return MockBackendClient()
