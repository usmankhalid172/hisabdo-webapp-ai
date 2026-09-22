import time

from src.config import get_settings
from src.schemas import ChatbotResponse


def make_payload(message, index="1"):
    return {
        "user_id": f"sept13-user-{index}",
        "message": message,
        "conversation_id": f"sept13-conversation-{index}",
        "history": [],
    }


def auth_headers():
    return {"X-Internal-Token": get_settings().internal_service_token}


SCENARIOS = [
    (
        "incomplete_input",
        "",
    ),
    (
        "urgent_symptoms",
        "I have severe chest pain and difficulty breathing.",
    ),
    (
        "multi_symptom",
        "I have headache, fever, cough, sore throat and body pain.",
    ),
    (
        "edge_case_text",
        "!!! ??? 12345 @@@ I feel weird %%%",
    ),
    (
        "normal_integration_query",
        "How can I manage my expenses?",
    ),
]


def test_real_world_scenario_matrix(client):
    for index, (name, message) in enumerate(SCENARIOS, start=1):
        response = client.post(
            "/api/v1/chatbot",
            json=make_payload(message, index),
            headers=auth_headers(),
        )

        # Empty input is expected to be rejected by request validation.
        if name == "incomplete_input":
            assert response.status_code == 422
            continue

        assert response.status_code == 200, name
        ChatbotResponse.model_validate(response.json())


def test_ai_integration_bug_regression(client):
    messages = [
        "What is a headache?",
        "I have headache and fever.",
        "What is the capital of Pakistan?",
    ]

    for index, message in enumerate(messages, start=1):
        response = client.post(
            "/api/v1/chatbot",
            json=make_payload(message, index),
            headers=auth_headers(),
        )

        assert response.status_code == 200
        body = response.json()

        ChatbotResponse.model_validate(body)
        assert body["conversation_id"] == f"sept13-conversation-{index}"
        assert isinstance(body["reply"], str)
        assert isinstance(body["source"], str)


def test_latency_benchmark(client):
    messages = [
        "I have severe chest pain and difficulty breathing.",
        "I have headache, fever and cough.",
        "What is the capital of Pakistan?",
        "I don't know what information to provide.",
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