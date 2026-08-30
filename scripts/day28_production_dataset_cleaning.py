"""
Production Dataset Cleaning & Pipeline Support Script (Day 28)
Project: HisabDo Web App AI
Intern: Rameesha Zafar
Task: Day 28 - Production Dataset Cleaning & Pipeline Support
"""

import json
import os
import sys

def clean_production_dataset(input_path, output_path):
    print("--- Starting Day 28 Production Dataset Cleaning & Pipeline Verification ---")

    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found at '{input_path}'. Generating clean fallback dataset.")
        return False

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("[ERROR] Input root must be a JSON array of transaction objects.")
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
    missing_value_count = 0
    duplicate_count = 0
    malformed_count = 0

    for idx, record in enumerate(data):
        is_valid = True
        tx_id = record.get("transaction_id")

        # 1. Deduplication
        if tx_id:
            if tx_id in seen_ids:
                duplicate_count += 1
                is_valid = False
            else:
                seen_ids.add(tx_id)
        else:
            missing_value_count += 1
            is_valid = False

        # 2. Schema Validation & Type Assertion
        for field, expected_type in required_schema.items():
            if field not in record or record[field] is None:
                missing_value_count += 1
                is_valid = False
            elif not isinstance(record[field], expected_type):
                malformed_count += 1
                is_valid = False

        # 3. Sanitization & Normalization
        if is_valid:
            record["amount"] = float(record["amount"])
            record["category"] = record["category"].strip().title()
            record["description"] = record["description"].strip()
            cleaned_records.append(record)

    # Export Sanitized Production Asset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_records, f, indent=2)

    print("\n--- Day 28 Production Cleaning Audit Summary ---")
    print(f"Total Input Records Audited: {len(data)}")
    print(f"Sanitized Production Records Exported: {len(cleaned_records)}")
    print(f"Duplicate Transactions Removed: {duplicate_count}")
    print(f"Missing Field Anomalies Filtered: {missing_value_count}")
    print(f"Malformed Type Anomalies Resolved: {malformed_count}")
    print(f"Production Asset Saved To: {output_path}")

    return True

if __name__ == "__main__":
    raw_path = os.path.join("data", "sample_transactions.json")
    prod_path = os.path.join("data", "cleaned_production_dataset_day28.json")
    clean_production_dataset(raw_path, prod_path)