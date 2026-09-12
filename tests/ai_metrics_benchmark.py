import os
import time
from statistics import mean

os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-token")
os.environ.setdefault("LLM_PROVIDER", "mock")

from fastapi.testclient import TestClient

from src.main import app


TEST_MESSAGES = [
    "How does automatic expense categorization work?",
    "What's the difference between profit and cash flow?",
    "How can I manage my expenses?",
    "How do I export my expenses?",
    "How can I track my spending?",
    "How do I categorize a restaurant expense?",
    "What is cash flow?",
    "How can I manage my budget?",
    "How can I view my expenses?",
    "How does the chatbot help with finances?",
]

AUTH_HEADERS = {
    "X-Internal-Token": os.environ.get("INTERNAL_SERVICE_TOKEN", "test-token")
}

client = TestClient(app)


def run_benchmark():
    results = []

    for index, message in enumerate(TEST_MESSAGES, start=1):
        payload = {
            "user_id": "benchmark-user",
            "message": message,
            "conversation_id": f"benchmark-{index}",
            "history": [],
        }

        start = time.perf_counter()

        response = client.post(
            "/api/v1/chatbot",
            json=payload,
            headers=AUTH_HEADERS,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        json_valid = False

        try:
            body = response.json()
            json_valid = response.status_code == 200 and isinstance(body, dict)
        except Exception:
            json_valid = False

        results.append(
            {
                "test_id": f"HTTP-LAT-{index:02d}",
                "http_status": response.status_code,
                "json_valid": json_valid,
                "latency_ms": round(elapsed_ms, 2),
            }
        )

    latencies = [result["latency_ms"] for result in results]

    valid_count = sum(result["json_valid"] for result in results)
    json_validity_rate = (valid_count / len(results)) * 100

    print("\n=== Sprint 1 AI Metrics Benchmark ===")
    print(f"Total HTTP tests: {len(results)}")
    print(f"Valid JSON responses: {valid_count}")
    print(f"JSON validity rate: {json_validity_rate:.2f}%")
    print(f"Average API latency: {mean(latencies):.2f} ms")
    print(f"Minimum API latency: {min(latencies):.2f} ms")
    print(f"Maximum API latency: {max(latencies):.2f} ms")

    print("\n--- Individual Results ---")
    for result in results:
        print(result)


if __name__ == "__main__":
    run_benchmark()