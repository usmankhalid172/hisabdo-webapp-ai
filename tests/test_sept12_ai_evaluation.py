import time
from concurrent.futures import ThreadPoolExecutor

from src.config import get_settings
from src.schemas import ChatbotResponse


def make_payload(message, index="1"):
    return {
        "user_id": f"sept12-user-{index}",
        "message": message,
        "conversation_id": f"sept12-conversation-{index}",
        "history": [],
    }


def auth_headers():
    return {"X-Internal-Token": get_settings().internal_service_token}


SCENARIOS = [
    ("vague_symptoms", "I don't feel well."),
    (
        "multiple_symptoms",
        "I have headache, fever, cough, sore throat and body pain.",
    ),
    (
        "emergency_trigger",
        "I am having severe chest pain and difficulty breathing.",
    ),
    ("off_topic", "What is the capital of Pakistan?"),
]


def test_comprehensive_patient_scenarios(client):
    for index, (name, message) in enumerate(SCENARIOS, start=1):
        response = client.post(
            "/api/v1/chatbot",
            json=make_payload(message, index),
            headers=auth_headers(),
        )

        assert response.status_code == 200, name
        ChatbotResponse.model_validate(response.json())


def test_json_structural_accuracy(client):
    expected_keys = {
        "reply",
        "conversation_id",
        "intent",
        "tokens_used",
        "source",
    }

    for index, (_, message) in enumerate(SCENARIOS, start=1):
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
    latencies = []

    for index, (_, message) in enumerate(SCENARIOS, start=1):
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


def test_concurrent_endpoint_stability(client):
    def send_request(item):
        index, (_, message) = item

        start = time.perf_counter()
        response = client.post(
            "/api/v1/chatbot",
            json=make_payload(message, index),
            headers=auth_headers(),
        )
        latency_ms = (time.perf_counter() - start) * 1000

        return response, latency_ms

    requests = [(index, scenario) for index, scenario in enumerate(SCENARIOS, 1)]

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(send_request, requests))

    latencies = []

    for response, latency_ms in results:
        assert response.status_code == 200
        ChatbotResponse.model_validate(response.json())
        latencies.append(latency_ms)

    print(f"\nConcurrent requests: {len(results)}")
    print(f"Average concurrent latency: {sum(latencies) / len(latencies):.2f} ms")
    print(f"Minimum concurrent latency: {min(latencies):.2f} ms")
    print(f"Maximum concurrent latency: {max(latencies):.2f} ms")

    assert len(results) == len(SCENARIOS)