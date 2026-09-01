"""
Day 25 - LLM Output Consistency Validator

Validates LLM response samples across multiple execution cycles.
Checks formatting consistency and flags invalid response patterns.
"""

import re


TEST_CASES = [
    {
        "id": "TC-01",
        "question": "How much did I spend on groceries?",
        "responses": [
            "You spent $250 on groceries this month.",
            "You spent $250 on groceries this month.",
            "You spent $250 on groceries this month.",
        ],
    },
    {
        "id": "TC-02",
        "question": "How much did I spend on transport?",
        "responses": [
            "You spent $120 on transport this month.",
            "You spent $120 on transport this month.",
            "You spent $120 on transport this month.",
        ],
    },
    {
        "id": "TC-03",
        "question": "What is my balance?",
        "responses": [
            "Your current balance is $850.",
            "Your current balance is $850.",
            "Your current balance is $850.",
        ],
    },
    {
        "id": "TC-04",
        "question": "Show my monthly spending.",
        "responses": [
            "Your monthly spending is $1,240.",
            "Your monthly spending is $1,240.",
            "Your monthly spending is $1,240.",
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


def validate_output(response, question):
    """Return None for a valid response or an error message."""

    if not response or not response.strip():
        return "Empty response"

    cleaned = response.strip()

    if not any(char.isalnum() for char in cleaned):
        return "Response contains no usable content"

    normalized_response = cleaned.lower().rstrip("?.! ")
    normalized_question = question.lower().strip().rstrip("?.! ")

    if normalized_response == normalized_question:
        return "Response is a bare echo of the question"

    if len(cleaned) < 3:
        return "Response is too short"

    if re.fullmatch(r"[\W_]+", cleaned):
        return "Response contains symbols only"

    return None


def main():
    print("LLM OUTPUT CONSISTENCY VALIDATION")
    print("=" * 40)

    total = 0
    passed = 0
    flagged = 0

    for test_case in TEST_CASES:
        print(f"\n{test_case['id']}: {test_case['question']}")

        valid_outputs = []
        case_flagged = False

        for cycle, response in enumerate(test_case["responses"], start=1):
            total += 1

            error = validate_output(
                response,
                test_case["question"]
            )

            if error:
                print(f"Cycle {cycle}: FLAG: {error}")
                flagged += 1
                case_flagged = True
            else:
                print(f"Cycle {cycle}: PASS")
                passed += 1
                valid_outputs.append(response.strip())

        # Check whether valid outputs are identical across cycles.
        if valid_outputs and len(set(valid_outputs)) > 1:
            print("Formatting/content consistency: INCONSISTENT")
            case_flagged = True
        elif valid_outputs:
            print("Formatting/content consistency: CONSISTENT")

        if case_flagged:
            print("Status: INCONSISTENCY / INVALID OUTPUT FLAGGED")
        else:
            print("Status: CONSISTENT")

    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)

    print(f"Total executions: {total}")
    print(f"Passed: {passed}")
    print(f"Flagged: {flagged}")

    pass_rate = (passed / total) * 100
    flag_rate = (flagged / total) * 100

    print(f"Validation pass rate: {pass_rate:.2f}%")
    print(f"Flag rate: {flag_rate:.2f}%")


if __name__ == "__main__":
    main()