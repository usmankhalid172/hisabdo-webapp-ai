from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.integration import routes
from src.integration.client import AIServiceClient
from src.integration.service import AIIntegrationService


app = FastAPI()
app.include_router(routes.router)

client = TestClient(app)


def test_chat_endpoint_rejects_empty_message():
    response = client.post(
        "/api/v1/ai/chat",
        json={"message": ""},
    )

    assert response.status_code == 422


def test_chat_endpoint_returns_ai_response(monkeypatch):
    mock_client = AIServiceClient(
        base_url="http://mock-ai-service"
    )

    async def fake_chat(payload):
        return {
            "status": "success",
            "response": "Your food spending is 5000 PKR.",
            "request_id": "req-001",
        }

    monkeypatch.setattr(mock_client, "chat", fake_chat)

    mock_service = AIIntegrationService(mock_client)

    monkeypatch.setattr(
        routes,
        "get_ai_service",
        lambda: mock_service,
    )

    response = client.post(
        "/api/v1/ai/chat",
        json={
            "message": "How much did I spend on food?",
            "conversation_id": "conv-001",
            "user_id": "user-001",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["response"] == "Your food spending is 5000 PKR."
    assert data["request_id"] == "req-001"