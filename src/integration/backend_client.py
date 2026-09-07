"""
Client for the application backend's financial data API.

Per Day 15 §6.1: exact user financial values (balance, expenses, revenue,
outstanding, etc.) must always come from authenticated backend/API data and
deterministic calculation — never from RAG retrieval.

The real backend data contract is not yet defined (Day 15 §10 blocker), so
per the Day 16 continuity plan this is mocked with a deterministic,
clearly-labelled stand-in. Swap `MockBackendClient` for a real HTTP client
once the contract lands — the interface (`get_user_financial_summary`)
is what the rest of the code depends on.
"""
from abc import ABC, abstractmethod
from functools import lru_cache


class BackendClient(ABC):
    @abstractmethod
    def get_user_financial_summary(self, user_id: str) -> dict:
        ...


class MockBackendClient(BackendClient):
    """Deterministic fake data, clearly marked as such, for POC/demo use."""

    def get_user_financial_summary(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "balance": 45230.50,
            "currency": "PKR",
            "total_expenses_this_month": 18420.00,
            "total_revenue_this_month": 62000.00,
            "outstanding_receivables": 9000.00,
            "source": "MOCK_BACKEND_CLIENT — replace once Day 15 §10 data contract is finalized",
        }


@lru_cache(maxsize=1)
def get_backend_client() -> BackendClient:
    """Return a process-wide singleton backend client.

    Cached (Task 27 backend-to-service layer optimization) so the client is
    built once and reused across requests instead of reconstructed on every
    chatbot call. Single seam to swap in a real HTTP-based client later.
    """
    return MockBackendClient()
