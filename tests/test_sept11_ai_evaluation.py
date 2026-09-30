import time

from src.config import get_settings
from src.main import app
from src.schemas import ChatbotResponse
from fastapi.testclient import TestClient


def make_payload(message, index="1"):
    return {
        "user_id": f"sept11-user-{index}",
        "message": message,
        "conversation_id": f"sept11-conversation-{index}",
        "history": [],
    }


def auth_headers():
    return {"X-Internal-Token": get_settings().internal_service_token}


def test_normal_query(client):
    response = client.post(
        "/api/v1/chatbot",
        json=make_payload("How can I manage my expenses?"),
        headers=auth_headers(),
    )

    assert response.status_code == 200
    ChatbotResponse.model_validate(response.json())


def test_multiple_symptoms(client):
    response = client.post(
        "/api/v1/chatbot",
        json=make_payload(
            "I have headache, fever, cough and sore throat."
        ),
        headers=auth_headers(),
    )

    assert response.status_code == 200
    ChatbotResponse.model_validate(response.json())


def test_missing_information_query(client):
    response = client.post(
        "/api/v1/chatbot",
        json=make_payload(
            "I do not know what information to provide."
        ),
        headers=auth_headers(),
    )

    assert response.status_code == 200
    ChatbotResponse.model_validate(response.json())


def test_non_medical_input(client):
    response = client.post(
        "/api/v1/chatbot",
        json=make_payload("What is the capital of Pakistan?"),
        headers=auth_headers(),
    )

    assert response.status_code == 200
    ChatbotResponse.model_validate(response.json())


def test_emergency_case(client):
    response = client.post(
        "/api/v1/chatbot",
        json=make_payload(
            "I am having severe chest pain and difficulty breathing."
        ),
        headers=auth_headers(),
    )

    assert response.status_code == 200
    ChatbotResponse.model_validate(response.json())


def test_json_format_consistency(client):
    messages = [
        "What is a headache?",
        "I have headache and fever.",
        "What is the capital of Pakistan?",
        "I need help with my information.",
        "I have severe chest pain and difficulty breathing.",
    ]

    expected_keys = {
        "reply",
        "conversation_id",
        "intent",
        "tokens_used",
        "source",
    }

    for index, message in enumerate(messages, start=1):
        response = client.post(
            "/api/v1/chatbot",
            json=make_payload(message, index),
            headers=auth_headers(),
        )

        assert response.status_code == 200
        body = response.json()

        assert set(body.keys()) == expected_keys
        ChatbotResponse.model_validate(body)


def test_latency_benchmark(client):
    messages = [
        "What is a headache?",
        "I have headache, fever and cough.",
        "What is the capital of Pakistan?",
        "I do not know what information to provide.",
        "I am having severe chest pain and difficulty breathing.",
    ]

    latencies = []

    for index, message in enumerate(messages, start=1):
        start = time.perf_counter()

        response = client.post(
            "/api/v1/chatbot",
            json=make_payload(message, index),
            headers=auth_headers(),
        )

        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

        assert response.status_code == 200
        ChatbotResponse.model_validate(response.json())

    print(f"\nLatency samples: {len(latencies)}")
    print(f"Average latency: {sum(latencies) / len(latencies):.2f} ms")
    print(f"Minimum latency: {min(latencies):.2f} ms")
    print(f"Maximum latency: {max(latencies):.2f} ms")

    assert all(latency >= 0 for latency in latencies)
