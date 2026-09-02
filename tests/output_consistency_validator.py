"""
Day 28 - Final LLM Response Regression & Consistency Audit

Runs multiple execution cycles for predefined LLM response test cases.
Checks:
1. Structural validity of responses
2. Output consistency across execution cycles
3. Formatting/content drift
4. Regression stability

This is a local regression test suite using representative response samples.
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


def validate_output(response, question):
    """
    Validate the basic structure of an LLM response.

    Returns:
        None if valid.
        Error message if invalid.
    """

    if not isinstance(response, str):
        return "Response is not a string"

    if not response.strip():
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


def check_consistency(responses):
    """
    Check whether valid responses remain identical across cycles.

    Returns:
        True if consistent.
        False if formatting/content drift is detected.
    """

    valid_outputs = [
        response.strip()
        for response in responses
        if isinstance(response, str) and response.strip()
    ]

    if len(valid_outputs) <= 1:
        return True

    return len(set(valid_outputs)) == 1


def main():
    print("DAY 28 - FINAL LLM RESPONSE REGRESSION & CONSISTENCY AUDIT")
    print("=" * 60)

    total_executions = 0
    passed = 0
    flagged = 0

    consistent_cases = 0
    drift_cases = 0
    structural_flag_cases = 0

    for test_case in TEST_CASES:
        print(f"\n{test_case['id']}: {test_case['question']}")
        print("-" * 60)

        case_flagged = False
        valid_outputs = []

        for cycle, response in enumerate(
            test_case["responses"],
            start=1
        ):
            total_executions += 1

            error = validate_output(
                response,
                test_case["question"]
            )

            if error:
                print(f"Cycle {cycle}: FLAG - {error}")
                flagged += 1
                case_flagged = True
            else:
                print(f"Cycle {cycle}: PASS")
                passed += 1
                valid_outputs.append(response.strip())

        # Check output consistency across valid cycles.
        if valid_outputs:
            if check_consistency(valid_outputs):
                print(
                    "Formatting/content consistency: CONSISTENT"
                )
            else:
                print(
                    "Formatting/content consistency: DRIFT DETECTED"
                )
                drift_cases += 1
                case_flagged = True
        else:
            print(
                "Formatting/content consistency: NOT EVALUATED"
            )

        if case_flagged:
            print("Status: ISSUE FLAGGED")

            if any(
                validate_output(
                    response,
                    test_case["question"]
                )
                for response in test_case["responses"]
            ):
                structural_flag_cases += 1
        else:
            print("Status: CONSISTENT")
            consistent_cases += 1

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL REGRESSION SUMMARY")
    print("=" * 60)

    print(f"Total test cases: {len(TEST_CASES)}")
    print(f"Total executions: {total_executions}")
    print(f"Passed executions: {passed}")
    print(f"Flagged executions: {flagged}")
    print(f"Consistent test cases: {consistent_cases}")
    print(f"Drift cases: {drift_cases}")
    print(f"Structural flag cases: {structural_flag_cases}")

    pass_rate = (passed / total_executions) * 100
    flag_rate = (flagged / total_executions) * 100

    print(f"Validation pass rate: {pass_rate:.2f}%")
    print(f"Validation flag rate: {flag_rate:.2f}%")

    print("\nRegression audit completed.")


if __name__ == "__main__":
    main()