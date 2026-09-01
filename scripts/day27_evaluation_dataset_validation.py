"""
Evaluation Dataset Validation & Data Pipeline Support Script (Day 27)
Project: HisabDo Web App AI
Intern: Rameesha Zafar
Task: Day 27 - Evaluation Dataset Validation & Data Pipeline Support
"""

import json
import os
import sys

def run_evaluation_dataset_validation(input_path, output_path):
    print(f"--- Starting Day 27 Evaluation Dataset Validation ---")

    if not os.path.exists(input_path):
        print(f"[ERROR] Input dataset file not found at '{input_path}'. Creating sample structure for validation.")
        return False

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("[ERROR] Dataset root must be a list of transaction objects.")
        return False

    required_schema = {
        "transaction_id": str,
        "user_id": str,
        "amount": (int, float),
        "category": str,
        "date": str,
        "description": str
    }

    cleaned_records = []
    seen_ids = set()
    null_value_errors = 0
    duplicate_errors = 0
    type_mismatch_errors = 0

    for idx, record in enumerate(data):
        is_valid = True
        tx_id = record.get("transaction_id")

        # Duplicate ID Check
        if tx_id:
            if tx_id in seen_ids:
                print(f"[WARNING] Duplicate transaction_id detected: {tx_id}")
                duplicate_errors += 1
                is_valid = False
            else:
                seen_ids.add(tx_id)

        # Field and Data Type Assertions
        for field, expected_type in required_schema.items():
            if field not in record or record[field] is None:
                print(f"[WARNING] Record {idx}: Missing field '{field}'")
                null_value_errors += 1
                is_valid = False
            elif not isinstance(record[field], expected_type):
                print(f"[WARNING] Record {idx}: Type mismatch for '{field}'")
                type_mismatch_errors += 1
                is_valid = False

        if is_valid:
            # Clean numerical amount and normalize string fields
            record["amount"] = float(record["amount"])
            record["category"] = record["category"].strip().title()
            cleaned_records.append(record)

    # Save Cleaned Evaluation Asset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_records, f, indent=2)

    print(f"\n--- Day 27 Evaluation Dataset Audit Summary ---")
    print(f"Total Input Records: {len(data)}")
    print(f"Cleaned Evaluation Records Exported: {len(cleaned_records)}")
    print(f"Null / Missing Value Anomalies Resolved: {null_value_errors}")
    print(f"Duplicate Record Anomalies Resolved: {duplicate_errors}")
    print(f"Data Type Mismatch Anomalies Resolved: {type_mismatch_errors}")
    print(f"Sanitized Evaluation Dataset Saved To: {output_path}")

    return True

if __name__ == "__main__":
    sample_in = os.path.join("data", "sample_transactions.json")
    eval_out = os.path.join("data", "cleaned_evaluation_dataset_day27.json")
    run_evaluation_dataset_validation(sample_in, eval_out)