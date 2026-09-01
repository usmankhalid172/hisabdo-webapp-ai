"""
Dataset Validation & Preprocessing Verification Script
Project: HisabDo Web App AI
Intern: Rameesha Zafar
Task: Day 23-24 Data Validation
"""

import json
import os
import sys


def validate_financial_dataset(file_path):
    print(f"--- Starting Dataset Validation: {file_path} ---")

    if not os.path.exists(file_path):
        print(
            f"[ERROR] Dataset file not found at '{file_path}'. Created placeholder validation check."
        )
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("[ERROR] Dataset root must be a list of transaction records.")
            return False

        required_fields = {
            "transaction_id": str,
            "user_id": str,
            "amount": (int, float),
            "category": str,
            "date": str,
            "description": str,
        }

        total_records = len(data)
        missing_value_count = 0
        type_mismatch_count = 0
        valid_records = 0

        for idx, record in enumerate(data):
            is_valid = True
            for field, expected_type in required_fields.items():
                if field not in record or record[field] is None:
                    print(
                        f"[WARNING] Record {idx}: Missing required field '{field}'"
                    )
                    missing_value_count += 1
                    is_valid = False
                elif not isinstance(record[field], expected_type):
                    print(
                        f"[WARNING] Record {idx}: Type mismatch for '{field}'. Expected {expected_type}, got {type(record[field])}"
                    )
                    type_mismatch_count += 1
                    is_valid = False

            if is_valid:
                valid_records += 1

        print(f"\n--- Validation Summary ---")
        print(f"Total Records Analyzed: {total_records}")
        print(f"Valid Records: {valid_records}")
        print(f"Missing Value Errors: {missing_value_count}")
        print(f"Data Type Mismatch Errors: {type_mismatch_count}")

        return (missing_value_count + type_mismatch_count) == 0

    except Exception as e:
        print(f"[ERROR] Failed to parse dataset: {str(e)}")
        return False


if __name__ == "__main__":
    sample_path = os.path.join("data", "sample_transactions.json")
    validate_financial_dataset(sample_path)