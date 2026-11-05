from src.financial_assistant import service
from src.schemas import ChatbotRequest


class FakeBackend:
    def __init__(self):
        self.requested_users = []

    def get_user_financial_summary(self, user_id):
        self.requested_users.append(user_id)

        summaries = {
            "customer-a": {
                "balance": "BALANCE_A_111",
                "currency": "PKR",
                "total_expenses_this_month": 1000,
                "total_revenue_this_month": 5000,
                "outstanding_receivables": 2000,
            },
            "customer-b": {
                "balance": "BALANCE_B_999",
                "currency": "PKR",
                "total_expenses_this_month": 9000,
                "total_revenue_this_month": 3000,
                "outstanding_receivables": 7000,
            },
        }

        return summaries[user_id]


class FakeProvider:
    def __init__(self):
        self.contexts = []

    def generate_reply(self, message, context=None, history=None):
        self.contexts.append(context)
        return "Synthetic financial response.", 0


def test_financial_data_is_isolated_between_two_users(monkeypatch):
    backend = FakeBackend()
    provider = FakeProvider()

    monkeypatch.setattr(
        service,
        "get_backend_client",
        lambda: backend,
    )
    monkeypatch.setattr(
        service,
        "get_llm_provider",
        lambda: provider,
    )

    request_a = ChatbotRequest(
        user_id="customer-a",
        message="What is my balance?",
        conversation_id="isolation-test-a",
        history=[],
    )

    request_b = ChatbotRequest(
        user_id="customer-b",
        message="What is my balance?",
        conversation_id="isolation-test-b",
        history=[],
    )

    response_a = service._handle_chat_impl(request_a)
    response_b = service._handle_chat_impl(request_b)

    assert backend.requested_users == [
        "customer-a",
        "customer-b",
    ]

    assert len(provider.contexts) == 2

    context_a = provider.contexts[0]
    context_b = provider.contexts[1]

    assert "BALANCE_A_111" in context_a
    assert "BALANCE_B_999" not in context_a

    assert "BALANCE_B_999" in context_b
    assert "BALANCE_A_111" not in context_b

    assert response_a.source == "backend_financial_api"
    assert response_b.source == "backend_financial_api"
