import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.expense_categorization.integration_readiness import (
    ExpenseIntegrationReadiness,
)


INPUT_PATH = ROOT / "data" / "day21_integration_test_cases.csv"
OUTPUT_PATH = ROOT / "data" / "day21_integration_results.csv"


def evaluate_cases():
    service = ExpenseIntegrationReadiness()

    results = []

    with INPUT_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            description = row["description"]
            expected_category = row["expected_category"]
            test_type = row["test_type"]

            result = {
                "description": description,
                "expected_category": expected_category,
                "test_type": test_type,
            }

            try:
                prediction = service.predict(description)

                predicted_category = prediction["category"]
                confidence = prediction["confidence"]
                accepted = prediction["accepted"]

                result.update(
                    {
                        "predicted_category": predicted_category,
                        "confidence": confidence,
                        "accepted": accepted,
                        "correct": (
                            bool(expected_category)
                            and predicted_category == expected_category
                        ),
                        "error": "",
                    }
                )

            except ValueError as exc:
                result.update(
                    {
                        "predicted_category": "",
                        "confidence": "",
                        "accepted": False,
                        "correct": False,
                        "error": str(exc),
                    }
                )

            results.append(result)

    fieldnames = [
        "description",
        "expected_category",
        "test_type",
        "predicted_category",
        "confidence",
        "accepted",
        "correct",
        "error",
    ]

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    valid_cases = [
        row for row in results
        if row["expected_category"]
    ]

    correct_predictions = [
        row for row in valid_cases
        if row["correct"]
    ]

    confidence_values = [
        float(row["confidence"])
        for row in valid_cases
        if row["confidence"] != ""
    ]

    accepted_predictions = [
        row for row in valid_cases
        if row["accepted"]
    ]

    print("Day 21–22 Integration Evaluation")
    print("--------------------------------")
    print("Total cases:", len(results))
    print("Cases with expected categories:", len(valid_cases))
    print("Correct predictions:", len(correct_predictions))

    if valid_cases:
        accuracy = len(correct_predictions) / len(valid_cases)
        print("Integration test accuracy:", round(accuracy, 4))

    if confidence_values:
        average_confidence = sum(confidence_values) / len(confidence_values)
        print("Average confidence:", round(average_confidence, 4))

    print("Accepted predictions:", len(accepted_predictions))
    print("Results saved to:", OUTPUT_PATH)

    print("\nDetailed Results")
    print("----------------")

    for row in results:
        print(
            f"{row['description']} -> "
            f"{row['predicted_category'] or 'ERROR'} | "
            f"confidence={row['confidence'] or 'N/A'} | "
            f"accepted={row['accepted']} | "
            f"correct={row['correct']} | "
            f"error={row['error'] or 'None'}"
        )


if __name__ == "__main__":
    evaluate_cases()