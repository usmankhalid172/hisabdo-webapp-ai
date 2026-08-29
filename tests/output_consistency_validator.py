"""
Day 27 - LLM Output Consistency and Structural Validation

Purpose:
- Run multiple cycles for identical inputs.
- Validate response content.
- Detect output drift.
- Validate basic response structure/schema.
- Log structural inconsistencies.

No live API calls are required. Responses are simulated so the
regression suite is deterministic and repeatable.
"""

from collections import Counter


TEST_CASES = [
    {
        "id": "TC-01",
        "question": "How much did I spend on groceries?",
        "responses": [
            "You spent $450 on groceries this month.",
            "You spent $450 on groceries this month.",
            "You spent $450 on groceries this month.",
        ],
    },
    {
        "id": "TC-02",
        "question": "How much did I spend on transport?",
        "responses": [
            "You spent $180 on transport this month.",
            "You spent $180 on transport this month.",
            "You spent $180 on transport this month.",
        ],
    },
    {
        "id": "TC-03",
        "question": "What is my balance?",
        "responses": [
            "Your current balance is $1,250.",
            "Your current balance is $1,250.",
            "Your current balance is $1,250.",
        ],
    },
    {
        "id": "TC-04",
        "question": "Show my monthly spending.",
        "responses": [
            "Your monthly spending is $850.",
            "Your monthly spending is $850.",
            "Your monthly spending is $850.",
        ],
    },
    {
        "id": "TC-05",
        "question": "How much did I spend?",
        "responses": [
            "You spent $620 this month.",
            "You spent $620 this month.",
            "You spent $620 this month.",
        ],
    },
    {
        "id": "TC-06",
        "question": "How much did I spend on food?",
        "responses": [
            "You spent $180 on food this month.",
            "You spent $180 on food this month.",
            "You spent $180 on Food this month.",
        ],
    },
]


def validate_response(question, response):
    """Validate content and basic output structure."""

    if not isinstance(response, str):
        return "Response is not a string"

    cleaned = response.strip()

    if not cleaned:
        return "Empty response"

    if not any(char.isalnum() for char in cleaned):
        return "Response contains no usable content"

    if cleaned.lower().rstrip("?.! ") == question.lower().rstrip("?.! "):
        return "Response is a bare echo of the question"

    # Basic structural/schema checks.
    if len(cleaned) < 5:
        return "Response is too short"

    if "\n\n\n\n" in cleaned:
        return "Unexpected excessive formatting"

    return "PASS"


def check_consistency(responses):
    """Check whether repeated outputs are identical."""

    normalized = [response.strip() for response in responses]

    if len(set(normalized)) == 1:
        return "CONSISTENT"

    return "DRIFT DETECTED"


def run_validation():
    total_executions = 0
    passed = 0
    flagged = 0
    consistent_cases = 0
    drift_cases = 0
    structural_bugs = 0

    print("DAY 27 - LLM OUTPUT CONSISTENCY & STRUCTURAL VALIDATION")
    print("=" * 58)

    for case in TEST_CASES:
        print(f"\n{case['id']}: {case['question']}")

        responses = case["responses"]
        total_executions += len(responses)

        for index, response in enumerate(responses, start=1):
            result = validate_response(case["question"], response)

            if result == "PASS":
                passed += 1
                print(f"Cycle {index}: PASS")
            else:
                flagged += 1
                structural_bugs += 1
                print(f"Cycle {index}: FLAG: {result}")

        consistency = check_consistency(responses)

        print(f"Formatting/content consistency: {consistency}")

        if consistency == "CONSISTENT":
            consistent_cases += 1
        else:
            drift_cases += 1

            counts = Counter(response.strip() for response in responses)

            print("Discrepancies:")
            for output, count in counts.items():
                print(f"  Occurrences: {count}")
                print(f"  Output: {output}")

        if consistency == "CONSISTENT":
            print("Status: CONSISTENT")
        else:
            print("Status: OUTPUT DRIFT FLAGGED")

    pass_rate = (passed / total_executions) * 100
    flag_rate = (flagged / total_executions) * 100

    print("\n" + "=" * 58)
    print("SUMMARY")
    print("=" * 58)
    print(f"Total executions: {total_executions}")
    print(f"Passed: {passed}")
    print(f"Flagged: {flagged}")
    print(f"Consistent test cases: {consistent_cases}")
    print(f"Formatting/content drift cases: {drift_cases}")
    print(f"Structural validation flags: {structural_bugs}")
    print(f"Validation pass rate: {pass_rate:.2f}%")
    print(f"Flag rate: {flag_rate:.2f}%")


if __name__ == "__main__":
    run_validation()