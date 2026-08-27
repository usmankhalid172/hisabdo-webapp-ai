"""
Dataset Validation & Preprocessing Verification Script (Day 25 - SQA Handover)
Project: HisabDo Web App AI
Intern: Rameesha Zafar
Task: Day 25 Dataset Validation & Preprocessing Verification
"""

import json
import os
import sys


def validate_and_preprocess_dataset(file_path):
    print(f"--- Starting Day 25 Dataset Validation: {file_path} ---")

    if not os.path.exists(file_path):
        print(
            f"[ERROR] Dataset file not found at '{file_path}'. Created placeholder validation check."
        )
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("[ERROR] Root data structure must be a JSON array.")
            return False

        required_fields = {
            "transaction_id": str,
            "user_id": str,
            "amount": (int, float),
            "category": str,
            "date": str,
            "description": str,
        }

        seen_ids = set()
        total_records = len(data)
        missing_values = 0
        type_mismatches = 0
        duplicate_entries = 0
        valid_records = 0

        for idx, record in enumerate(data):
            is_valid = True

            # Duplicate Check
            tx_id = record.get("transaction_id")
            if tx_id:
                if tx_id in seen_ids:
                    print(f"[WARNING] Duplicate transaction_id found: {tx_id}")
                    duplicate_entries += 1
                    is_valid = False
                else:
                    seen_ids.add(tx_id)

            # Field & Type Checks
            for field, expected_type in required_fields.items():
                if field not in record or record[field] is None:
                    print(
                        f"[WARNING] Record {idx}: Missing field '{field}'"
                    )
                    missing_values += 1
                    is_valid = False
                elif not isinstance(record[field], expected_type):
                    print(
                        f"[WARNING] Record {idx}: Type mismatch for '{field}'"
                    )
                    type_mismatches += 1
                    is_valid = False

            if is_valid:
                valid_records += 1

        print(f"\n--- Day 25 Validation & Audit Summary ---")
        print(f"Total Records Analyzed: {total_records}")
        print(f"Valid Records: {valid_records}")
        print(f"Missing Value Errors: {missing_values}")
        print(f"Type Mismatch Errors: {type_mismatches}")
        print(f"Duplicate Record Errors: {duplicate_entries}")

        passed = (missing_values + type_mismatches + duplicate_entries) == 0
        print(f"Overall SQA Handover Status: {'PASSED' if passed else 'FAILED'}")
        return passed

    except Exception as e:
        print(f"[ERROR] Parsing failed: {str(e)}")
        return False


if __name__ == "__main__":
    sample_path = os.path.join("data", "sample_transactions.json")
    validate_and_preprocess_dataset(sample_path)