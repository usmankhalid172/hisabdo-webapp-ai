from src.financial_assistant import service
from src.schemas import ChatbotRequest


class SyntheticBackend:
    def __init__(self):
        self.requested_user_ids = []

    def get_user_financial_summary(self, user_id):
        self.requested_user_ids.append(user_id)

        summaries = {
            "customer-a": {
                "balance": 1111,
                "currency": "PKR",
                "total_expenses_this_month": 111,
                "total_revenue_this_month": 11111,
                "outstanding_receivables": 1111,
            },
            "customer-b": {
                "balance": 2222,
                "currency": "PKR",
                "total_expenses_this_month": 222,
                "total_revenue_this_month": 22222,
                "outstanding_receivables": 2222,
            },
        }
        return summaries[user_id]


class SyntheticProvider:
    def __init__(self):
        self.contexts = []

    def generate_reply(self, message, context=None, history=None):
        self.contexts.append(context)
        return "Synthetic test response", 1


def test_financial_context_is_isolated_between_two_users(monkeypatch):
    backend = SyntheticBackend()
    provider = SyntheticProvider()

    monkeypatch.setattr(
        service, "get_backend_client", lambda: backend
    )
    monkeypatch.setattr(
        service, "get_llm_provider", lambda: provider
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

    assert backend.requested_user_ids == ["customer-a", "customer-b"]
    assert len(provider.contexts) == 2

    context_a = provider.contexts[0]
    context_b = provider.contexts[1]

    assert "1111" in context_a
    assert "2222" not in context_a

    assert "2222" in context_b
    assert "1111" not in context_b

    assert response_a.source == "backend_financial_api"
    assert response_b.source == "backend_financial_api"
