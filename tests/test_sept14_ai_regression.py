import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

from src.config import get_settings
from src.schemas import ChatbotResponse


def make_payload(message, index="1"):
    return {
        "user_id": f"sept14-user-{index}",
        "message": message,
        "conversation_id": f"sept14-conversation-{index}",
        "history": [],
    }


def auth_headers():
    return {"X-Internal-Token": get_settings().internal_service_token}


REGRESSION_CASES = [
    "How can I manage my expenses?",
    "What is a headache?",
    "I have headache, fever and cough.",
    "I do not know what information to provide.",
    "What is the capital of Pakistan?",
    "I am having severe chest pain and difficulty breathing.",
]


def send_request(client, message, index):
    start = time.perf_counter()

    response = client.post(
        "/api/v1/chatbot",
        json=make_payload(message, index),
        headers=auth_headers(),
    )

    latency_ms = (time.perf_counter() - start) * 1000
    return response, latency_ms


def test_full_regression_suite(client):
    """Verify representative AI assistant scenarios still work."""
    for index, message in enumerate(REGRESSION_CASES, start=1):
        response, _ = send_request(client, message, index)

        assert response.status_code == 200
        body = response.json()

        ChatbotResponse.model_validate(body)

        assert isinstance(body["reply"], str)
        assert isinstance(body["source"], str)
        assert body["conversation_id"] == f"sept14-conversation-{index}"


def test_json_payload_consistency(client):
    """Verify every successful response has the same JSON structure."""
    expected_keys = {
        "reply",
        "conversation_id",
        "intent",
        "tokens_used",
        "source",
    }

    for index, message in enumerate(REGRESSION_CASES, start=1):
        response, _ = send_request(client, message, index)

        assert response.status_code == 200

        body = response.json()

        assert set(body.keys()) == expected_keys
        ChatbotResponse.model_validate(body)


def test_latency_benchmark(client):
    """Measure sequential response latency."""
    latencies = []

    for index, message in enumerate(REGRESSION_CASES, start=1):
        response, latency_ms = send_request(client, message, index)

        assert response.status_code == 200
        ChatbotResponse.model_validate(response.json())

        latencies.append(latency_ms)

    print(f"\nLatency samples: {len(latencies)}")
    print(f"Average latency: {mean(latencies):.2f} ms")
    print(f"Minimum latency: {min(latencies):.2f} ms")
    print(f"Maximum latency: {max(latencies):.2f} ms")

    assert all(latency >= 0 for latency in latencies)


def test_concurrent_multi_user_benchmark(client):
    """Benchmark concurrent requests from multiple simulated users."""
    requests = [
        (index, message)
        for index, message in enumerate(REGRESSION_CASES, start=1)
    ]

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(
            executor.map(
                lambda item: send_request(client, item[1], item[0]),
                requests,
            )
        )

    total_time = time.perf_counter() - start

    latencies = []

    for response, latency_ms in results:
        assert response.status_code == 200
        ChatbotResponse.model_validate(response.json())
        latencies.append(latency_ms)

    throughput = len(results) / total_time if total_time > 0 else 0

    print(f"\nConcurrent users: {len(results)}")
    print(f"Total concurrent time: {total_time * 1000:.2f} ms")
    print(f"Average concurrent latency: {mean(latencies):.2f} ms")
    print(f"Minimum concurrent latency: {min(latencies):.2f} ms")
    print(f"Maximum concurrent latency: {max(latencies):.2f} ms")
    print(f"Throughput: {throughput:.2f} requests/sec")

    assert len(results) == len(REGRESSION_CASES)
    assert all(response.status_code == 200 for response, _ in results)
    assert all(latency >= 0 for latency in latencies)
    assert throughput > 0