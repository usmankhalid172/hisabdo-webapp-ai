"""
Dataset Preprocessing & Categorization Support Script (Day 26)
Project: HisabDo Web App AI
Intern: Rameesha Zafar
Task: Day 26 - Dataset Preprocessing & Categorization Support
"""

import json
import os
import re

def preprocess_and_categorize_dataset(input_path, output_path):
    print(f"--- Starting Day 26 Preprocessing & Categorization Support ---")
    
    if not os.path.exists(input_path):
        print(f"[ERROR] Input dataset not found at '{input_path}'. Creating placeholder report.")
        return False

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Keywords for fallback rule-based categorization support
    category_rules = {
        "Groceries": ["supermarket", "grocery", "mart", "store", "provisions", "milk", "vegetables"],
        "Transportation": ["uber", "careem", "taxi", "fuel", "petrol", "cab", "commute", "bus"],
        "Utilities": ["electric", "bill", "k-electric", "water", "gas", "internet", "recharge", "mobile"],
        "Healthcare": ["pharmacy", "doctor", "clinic", "medicine", "hospital", "lab"],
        "Food": ["restaurant", "burger", "pizza", "cafe", "dinner", "lunch", "food"],
        "Rent": ["rent", "landlord", "apartment", "maintenance"]
    }

    cleaned_data = []
    seen_ids = set()
    missing_count = 0
    duplicate_count = 0
    categorized_count = 0

    for idx, record in enumerate(data):
        tx_id = record.get("transaction_id")
        
        # Deduplication
        if tx_id in seen_ids:
            duplicate_count += 1
            continue
        seen_ids.add(tx_id)

        # Missing values check
        if not record.get("amount") or not record.get("description"):
            missing_count += 1
            continue

        # Categorization Support & Pipeline Normalization
        current_cat = record.get("category", "").strip().title()
        desc = record.get("description", "").lower()

        if not current_cat or current_cat == "Uncategorized":
            assigned_cat = "Uncategorized"
            for cat, keywords in category_rules.items():
                if any(kw in desc for kw in keywords):
                    assigned_cat = cat
                    categorized_count += 1
                    break
            record["category"] = assigned_cat
        else:
            record["category"] = current_cat

        # Clean numerical amount
        record["amount"] = float(record["amount"])
        cleaned_data.append(record)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)

    print(f"\n--- Day 26 Preprocessing & Cleaning Summary ---")
    print(f"Total Input Records: {len(data)}")
    print(f"Cleaned Output Records: {len(cleaned_data)}")
    print(f"Duplicates Removed: {duplicate_count}")
    print(f"Missing Value Records Dropped: {missing_count}")
    print(f"Auto-Categorized Support Records: {categorized_count}")
    print(f"Clean Dataset Saved to: {output_path}")

    return True

if __name__ == "__main__":
    in_path = os.path.join("data", "sample_transactions.json")
    out_path = os.path.join("data", "cleaned_transactions_day26.json")
    preprocess_and_categorize_dataset(in_path, out_path)