import json
import time
from statistics import mean

from src.financial_assistant.service import handle_chat
from src.schemas import ChatbotRequest, ChatbotResponse


TEST_MESSAGES = [
    "How does automatic expense categorization work?",
    "What's the difference between profit and cash flow?",
    "How can I manage my expenses?",
]


def run_benchmark():
    results = []

    for index, message in enumerate(TEST_MESSAGES, start=1):
        request = ChatbotRequest(
            user_id="benchmark-user",
            message=message,
            conversation_id=f"benchmark-{index}",
            history=[],
        )

        start = time.perf_counter()
        response = handle_chat(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        json_valid = True
        try:
            ChatbotResponse.model_validate(response)
            json.dumps(response.model_dump())
        except Exception:
            json_valid = False

        results.append(
            {
                "test_id": f"JSON-LAT-{index:02d}",
                "json_valid": json_valid,
                "latency_ms": round(elapsed_ms, 2),
                "source": response.source,
                "intent": response.intent,
            }
        )

    latencies = [result["latency_ms"] for result in results]

    valid_count = sum(result["json_valid"] for result in results)
    json_validity_rate = (valid_count / len(results)) * 100

    print("\n=== AI Metrics Benchmark ===")
    print(f"Total tests: {len(results)}")
    print(f"Valid JSON responses: {valid_count}")
    print(f"JSON validity rate: {json_validity_rate:.2f}%")
    print(f"Average latency: {mean(latencies):.2f} ms")
    print(f"Minimum latency: {min(latencies):.2f} ms")
    print(f"Maximum latency: {max(latencies):.2f} ms")

    print("\n--- Individual Results ---")
    for result in results:
        print(result)


if __name__ == "__main__":
    run_benchmark()
