#!/usr/bin/env python3
"""Validate the Department 3 standardized knowledge export (Python stdlib only)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cleaned_knowledge_records.json"
REQUIRED = {
    "id", "title", "section", "category", "source_url", "language",
    "last_updated", "product_module", "content", "source_reference",
    "source_verification_status", "content_review_status", "last_reviewed",
    "version", "ingestion_eligibility",
}

def main():
    records = json.loads(DATA.read_text(encoding="utf-8"))
    assert isinstance(records, list), "Top-level JSON value must be an array"
    ids = []
    for i, record in enumerate(records):
        missing = REQUIRED - record.keys()
        assert not missing, f"Record {i} missing keys: {sorted(missing)}"
        for key in ("id", "title", "section", "category", "language",
                    "product_module", "content", "version"):
            assert isinstance(record[key], str) and record[key].strip(), (
                f"Record {i}: {key} must be a non-empty string"
            )
        assert record["source_verification_status"] in {
            "metadata_marked_verified", "unverified"
        }, f"Record {i}: invalid source_verification_status"
        assert record["ingestion_eligibility"] in {
            "hold_pending_independent_owner_approval", "eligible_after_approval"
        }, f"Record {i}: invalid ingestion_eligibility"
        assert record["source_url"] is None or isinstance(record["source_url"], str)
        ids.append(record["id"])
    assert len(ids) == len(set(ids)), "Duplicate record IDs found"
    assert len(records) == 20, f"Expected 20 source JSON records, got {len(records)}"
    print(f"PASS: {len(records)} records; required metadata present; IDs unique.")
    print("NOTE: Production ingestion remains on hold pending independent owner approval.")

if __name__ == "__main__":
    main()
