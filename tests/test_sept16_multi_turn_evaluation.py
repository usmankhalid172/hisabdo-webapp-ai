import time
from statistics import mean

from src.schemas import ChatbotResponse


MULTI_TURN_SCENARIOS = [
    {
        "name": "headache_follow_up",
        "user_id": "sept16-patient-1",
        "conversation_id": "sept16-conversation-1",
        "turns": [
            "I have been having a headache since this morning.",
            "The headache is still there. What information should I provide?",
            "I also have a mild fever.",
        ],
    },
    {
        "name": "cough_follow_up",
        "user_id": "sept16-patient-2",
        "conversation_id": "sept16-conversation-2",
        "turns": [
            "I have been coughing since yesterday.",
            "The cough is getting worse. What should I tell you about it?",
            "I also feel tired and have a mild fever.",
        ],
    },
    {
        "name": "chest_discomfort_follow_up",
        "user_id": "sept16-patient-3",
        "conversation_id": "sept16-conversation-3",
        "turns": [
            "I am having chest discomfort.",
            "The discomfort is still present. What other details are important?",
            "I am also having difficulty breathing.",
        ],
    },
]


EXPECTED_KEYS = {
    "reply",
    "conversation_id",
    "intent",
    "tokens_used",
    "source",
}


def send_turn(client, scenario, message, history):
    payload = {
        "user_id": scenario["user_id"],
        "message": message,
        "conversation_id": scenario["conversation_id"],
        "history": history,
    }

    start = time.perf_counter()

    response = client.post(
        "/api/v1/chatbot",
        json=payload,
        headers={"X-Internal-Token": "test-token"},
    )

    latency_ms = (time.perf_counter() - start) * 1000

    return response, latency_ms


def test_multi_turn_patient_scenarios(client):
    """Verify consecutive patient turns return valid chatbot responses."""
    total_turns = 0
    successful_turns = 0

    for scenario in MULTI_TURN_SCENARIOS:
        history = []

        for message in scenario["turns"]:
            response, _ = send_turn(
                client,
                scenario,
                message,
                history,
            )

            total_turns += 1

            assert response.status_code == 200

            body = response.json()
            ChatbotResponse.model_validate(body)

            assert body["conversation_id"] == scenario["conversation_id"]
            assert isinstance(body["reply"], str)
            assert body["reply"].strip()

            successful_turns += 1

            history.append(
                {
                    "role": "user",
                    "content": message,
                }
            )
            history.append(
                {
                    "role": "assistant",
                    "content": body["reply"],
                }
            )

    print(f"\nTotal multi-turn requests: {total_turns}")
    print(f"Successful requests: {successful_turns}")

    assert successful_turns == total_turns


def test_context_retention_flow(client):
    """
    Verify that conversation history can be passed through consecutive calls.

    The current MockLLMProvider intentionally ignores history, so this test
    validates context transmission and conversation continuity rather than
    semantic memory.
    """
    for scenario in MULTI_TURN_SCENARIOS:
        history = []

        for turn_number, message in enumerate(scenario["turns"], start=1):
            response, _ = send_turn(
                client,
                scenario,
                message,
                history,
            )

            assert response.status_code == 200

            body = response.json()
            ChatbotResponse.model_validate(body)

            assert body["conversation_id"] == scenario["conversation_id"]

            if turn_number > 1:
                assert len(history) >= 2

            history.append(
                {
                    "role": "user",
                    "content": message,
                }
            )
            history.append(
                {
                    "role": "assistant",
                    "content": body["reply"],
                }
            )

        assert len(history) == len(scenario["turns"]) * 2


def test_multi_turn_json_payload_consistency(client):
    """Verify JSON payload structure remains stable across all turns."""
    for scenario in MULTI_TURN_SCENARIOS:
        history = []

        for message in scenario["turns"]:
            response, _ = send_turn(
                client,
                scenario,
                message,
                history,
            )

            assert response.status_code == 200

            body = response.json()

            assert set(body.keys()) == EXPECTED_KEYS
            ChatbotResponse.model_validate(body)

            history.append(
                {
                    "role": "user",
                    "content": message,
                }
            )
            history.append(
                {
                    "role": "assistant",
                    "content": body["reply"],
                }
            )


def test_multi_turn_latency_benchmark(client):
    """Benchmark latency across consecutive multi-turn patient calls."""
    latencies = []

    for scenario in MULTI_TURN_SCENARIOS:
        history = []

        for message in scenario["turns"]:
            response, latency_ms = send_turn(
                client,
                scenario,
                message,
                history,
            )

            assert response.status_code == 200
            ChatbotResponse.model_validate(response.json())

            latencies.append(latency_ms)

            body = response.json()

            history.append(
                {
                    "role": "user",
                    "content": message,
                }
            )
            history.append(
                {
                    "role": "assistant",
                    "content": body["reply"],
                }
            )

    print(f"\nMulti-turn latency samples: {len(latencies)}")
    print(f"Average latency: {mean(latencies):.2f} ms")
    print(f"Minimum latency: {min(latencies):.2f} ms")
    print(f"Maximum latency: {max(latencies):.2f} ms")

    assert len(latencies) == 9
    assert all(latency >= 0 for latency in latencies)