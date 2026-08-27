import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.financial_assistant.llm_service import validate_llm_response


TEST_CASES = [
    {
        "id": "TC-01",
        "question": "How much did I spend on groceries?",
        "responses": [
            "You spent $200 on groceries this month.",
            "You spent $200 on groceries this month.",
            "You spent $200 on groceries this month.",
        ],
    },
    {
        "id": "TC-02",
        "question": "How much did I spend on transport?",
        "responses": [
            "You spent $150 on transport.",
            "Your transport spending was $150.",
            "You spent $150 on transportation.",
        ],
    },
    {
        "id": "TC-03",
        "question": "What is my balance?",
        "responses": [
            "Your current balance is $500.",
            "Your current balance is $500.",
            "Your balance is currently $500.",
        ],
    },
    {
        "id": "TC-04",
        "question": "Show my monthly spending.",
        "responses": [
            "Your monthly spending is $1,200.",
            "Your monthly spending is $1,200.",
            "Your monthly spending is $1,200.",
        ],
    },
    {
        "id": "TC-05",
        "question": "How much did I spend?",
        "responses": [
            "",
            "...",
            "How much did I spend?",
        ],
    },
]


def validate_response(response, question):
    try:
        validate_llm_response(response, user_question=question)
        return "PASS"
    except Exception as exc:
        return f"FLAG: {exc}"


def main():
    total = 0
    passed = 0
    flagged = 0

    print("LLM OUTPUT CONSISTENCY VALIDATION")
    print("=" * 40)

    for case in TEST_CASES:
        print(f"\n{case['id']}: {case['question']}")

        results = []

        for cycle, response in enumerate(case["responses"], start=1):
            result = validate_response(response, case["question"])
            results.append(result)

            print(f"Cycle {cycle}: {result}")

            total += 1

            if result == "PASS":
                passed += 1
            else:
                flagged += 1

        valid_results = [r for r in results if r == "PASS"]

        if len(valid_results) != len(results):
            print("Status: INCONSISTENCY / INVALID OUTPUT FLAGGED")
        else:
            print("Status: CONSISTENT")

    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    print("Total executions:", total)
    print("Passed:", passed)
    print("Flagged:", flagged)

    if total:
        print("Validation pass rate:", f"{(passed / total) * 100:.2f}%")
        print("Flag rate:", f"{(flagged / total) * 100:.2f}%")


if __name__ == "__main__":
    main()