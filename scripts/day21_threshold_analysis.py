import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "data" / "day21_integration_results.csv"

THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70]


def main():
    with RESULTS_PATH.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    rows = [
        row
        for row in rows
        if row["expected_category"]
    ]

    print("Confidence Threshold Analysis")
    print("-----------------------------")
    print("Labeled cases:", len(rows))
    print()

    for threshold in THRESHOLDS:
        accepted = [
            row
            for row in rows
            if float(row["confidence"]) >= threshold
        ]

        correct_accepted = [
            row
            for row in accepted
            if row["correct"] == "True"
        ]

        incorrect_accepted = [
            row
            for row in accepted
            if row["correct"] != "True"
        ]

        acceptance_rate = (
            len(accepted) / len(rows)
            if rows
            else 0
        )

        accepted_accuracy = (
            len(correct_accepted) / len(accepted)
            if accepted
            else 0
        )

        print(f"Threshold: {threshold:.2f}")
        print(f"  Accepted: {len(accepted)}")
        print(f"  Correct accepted: {len(correct_accepted)}")
        print(f"  Incorrect accepted: {len(incorrect_accepted)}")
        print(f"  Acceptance rate: {acceptance_rate:.2%}")
        print(f"  Accuracy among accepted: {accepted_accuracy:.2%}")
        print()


if __name__ == "__main__":
    main()
