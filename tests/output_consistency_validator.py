"""
Day 26 - LLM Output Consistency Validator

Runs repeated evaluations for identical inputs and checks:
- Output validity
- Exact output consistency
- Formatting drift
- Response discrepancies
"""

from collections import Counter
import re


TEST_CASES = [
    {
        "id": "TC-01",
        "input": "How much did I spend on groceries?",
        "outputs": [
            "You spent $250 on groceries this month.",
            "You spent $250 on groceries this month.",
            "You spent $250 on groceries this month.",
        ],
    },
    {
        "id": "TC-02",
        "input": "What is my current balance?",
        "outputs": [
            "Your current balance is $850.",
            "Your current balance is $850.",
            "Your current balance is $850.",
        ],
    },
    {
        "id": "TC-03",
        "input": "Show my monthly spending.",
        "outputs": [
            "Your monthly spending is $1,240.",
            "Your monthly spending is $1,240.",
            "Your monthly spending is $1,240.",
        ],
    },
    {
        "id": "TC-04",
        "input": "How much did I spend on transport?",
        "outputs": [
            "You spent $120 on transport this month.",
            "You spent $120 on transport this month.",
            "You spent $120 on transport this month.",
        ],
    },
    {
        "id": "TC-05",
        "input": "How much did I spend?",
        "outputs": [
            "You spent $500 this month.",
            "You spent $500 this month.",
            "You spent $500 this month.",
        ],
    },
    {
        "id": "TC-06",
        "input": "How much did I spend on food?",
        "outputs": [
            "You spent $180 on food this month.",
            "You spent $180 on food this month.",
            "You spent $180 on Food this month.",
        ],
    },
]


def validate_output(output, user_input):
    """Return an error message if the output is invalid."""

    if not output or not output.strip():
        return "Empty response"

    cleaned = output.strip()

    if not any(char.isalnum() for char in cleaned):
        return "Response contains no usable content"

    normalized_output = cleaned.lower().rstrip("?.! ")
    normalized_input = user_input.lower().strip().rstrip("?.! ")

    if normalized_output == normalized_input:
        return "Response is a bare echo of the input"

    if re.fullmatch(r"[\W_]+", cleaned):
        return "Response contains symbols only"

    return None


def normalize_formatting(output):
    """
    Normalize harmless formatting differences while preserving
    meaningful text differences.
    """
    return " ".join(output.strip().split())


def main():
    print("DAY 26 - LLM OUTPUT CONSISTENCY VALIDATION")
    print("=" * 50)

    total_cycles = 0
    passed_cycles = 0
    flagged_cycles = 0
    consistent_cases = 0
    drift_cases = 0

    discrepancies = []

    for test_case in TEST_CASES:
        test_id = test_case["id"]
        user_input = test_case["input"]
        outputs = test_case["outputs"]

        print(f"\n{test_id}: {user_input}")

        normalized_outputs = []

        for cycle, output in enumerate(outputs, start=1):
            total_cycles += 1

            error = validate_output(output, user_input)

            if error:
                print(f"Cycle {cycle}: FLAG: {error}")
                flagged_cycles += 1
            else:
                print(f"Cycle {cycle}: PASS")
                passed_cycles += 1
                normalized_outputs.append(normalize_formatting(output))

        if normalized_outputs:
            unique_outputs = set(normalized_outputs)

            if len(unique_outputs) == 1:
                print("Consistency: CONSISTENT")
                consistent_cases += 1
            else:
                print("Consistency: DRIFT DETECTED")
                drift_cases += 1

                counts = Counter(normalized_outputs)

                discrepancies.append(
                    {
                        "id": test_id,
                        "input": user_input,
                        "outputs": list(unique_outputs),
                        "counts": dict(counts),
                    }
                )

        else:
            print("Consistency: INVALID OUTPUTS")

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    print(f"Total executions: {total_cycles}")
    print(f"Passed: {passed_cycles}")
    print(f"Flagged: {flagged_cycles}")
    print(f"Consistent test cases: {consistent_cases}")
    print(f"Formatting/content drift cases: {drift_cases}")

    validation_rate = (passed_cycles / total_cycles) * 100

    print(f"Validation pass rate: {validation_rate:.2f}%")

    print("\nDISCREPANCIES")
    print("-" * 50)

    if discrepancies:
        for item in discrepancies:
            print(f"\n{item['id']}: {item['input']}")

            for output, count in item["counts"].items():
                print(f"  Occurrences: {count}")
                print(f"  Output: {output}")
    else:
        print("No discrepancies detected.")


if __name__ == "__main__":
    main()