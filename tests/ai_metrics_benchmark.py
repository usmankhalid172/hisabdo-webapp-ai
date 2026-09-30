import os
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-token")
os.environ.setdefault("LLM_PROVIDER", "mock")

from fastapi.testclient import TestClient

from src.main import app
from src.schemas import ChatbotResponse


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


def send_request(test_id, message, user_id):
    client = TestClient(app)

    payload = {
        "user_id": user_id,
        "message": message,
        "conversation_id": f"{user_id}-{test_id}",
        "history": [],
    }

    start = time.perf_counter()

    try:
        response = client.post(
            "/api/v1/chatbot",
            json=payload,
            headers=AUTH_HEADERS,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        schema_valid = False

        try:
            body = response.json()

            if response.status_code == 200:
                ChatbotResponse.model_validate(body)
                schema_valid = True
        except Exception:
            schema_valid = False

        return {
            "test_id": test_id,
            "user_id": user_id,
            "http_status": response.status_code,
            "schema_valid": schema_valid,
            "latency_ms": round(elapsed_ms, 2),
        }

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "test_id": test_id,
            "user_id": user_id,
            "http_status": "ERROR",
            "schema_valid": False,
            "latency_ms": round(elapsed_ms, 2),
            "error": str(exc),
        }


def run_sequential_benchmark():
    results = []

    for index, message in enumerate(TEST_MESSAGES, start=1):
        results.append(
            send_request(
                test_id=f"HTTP-LAT-{index:02d}",
                message=message,
                user_id="benchmark-user",
            )
        )

    return results


def run_concurrent_benchmark():
    concurrent_requests = [
        (
            f"HTTP-CON-{index:02d}",
            message,
            f"benchmark-user-{index:02d}",
        )
        for index, message in enumerate(TEST_MESSAGES, start=1)
    ]

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(send_request, test_id, message, user_id)
            for test_id, message, user_id in concurrent_requests
        ]

        results = [future.result() for future in futures]

    total_elapsed_seconds = time.perf_counter() - start

    return results, total_elapsed_seconds


def print_summary(results, title):
    latencies = [result["latency_ms"] for result in results]

    valid_count = sum(result["schema_valid"] for result in results)
    successful_count = sum(result["http_status"] == 200 for result in results)

    json_schema_rate = (valid_count / len(results)) * 100
    success_rate = (successful_count / len(results)) * 100

    print(f"\n=== {title} ===")
    print(f"Total requests: {len(results)}")
    print(f"HTTP 200 responses: {successful_count}")
    print(f"Successful response rate: {success_rate:.2f}%")
    print(f"Schema-valid responses: {valid_count}")
    print(f"JSON schema validity rate: {json_schema_rate:.2f}%")
    print(f"Average latency: {mean(latencies):.2f} ms")
    print(f"Minimum latency: {min(latencies):.2f} ms")
    print(f"Maximum latency: {max(latencies):.2f} ms")

    print("\n--- Individual Results ---")

    for result in results:
        print(result)


def run_benchmark():
    sequential_results = run_sequential_benchmark()

    print_summary(
        sequential_results,
        "Sequential HTTP API Benchmark",
    )

    concurrent_results, total_elapsed_seconds = run_concurrent_benchmark()

    print_summary(
        concurrent_results,
        "Concurrent Multi-User Throughput Benchmark",
    )

    throughput = len(concurrent_results) / total_elapsed_seconds

    print(f"\nConcurrent batch duration: {total_elapsed_seconds:.4f} seconds")
    print(f"Throughput: {throughput:.2f} requests/second")


if __name__ == "__main__":
    run_benchmark()
