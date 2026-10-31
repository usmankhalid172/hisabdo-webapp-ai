"""Privacy gate: the chatbot's knowledge base must not contain personal identifiers.

See docs/dept3-knowledge-source-audit.md, section 4.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from kb_privacy_scan import LIVE_KB, scan_file, scan_json_keys, scan_text  # noqa: E402


def test_live_knowledge_base_has_no_personal_identifiers():
    for path in LIVE_KB:
        findings = [h for h in scan_file(path) if "(allowed" not in h[1]]
        assert findings == [], f"{path.name}: {findings}"


def test_scanner_detects_identifiers_it_must_block():
    """Positive control: if the scanner stopped detecting these, the test above would pass for nothing."""
    review = "Great app! - posted by Ayesha, ayesha.k@mail.example, 0301-2345678, CNIC 35202-1234567-1"
    kinds = {kind for kind, _ in scan_text(review)}
    assert {"email", "pk_phone", "cnic"} <= kinds
    assert scan_json_keys({"reviews": [{"reviewer_name": "Someone", "text": "ok"}]}) == [
        ("identity_field", "$.reviews[0].reviewer_name")]


def test_official_support_address_is_allowed():
    assert all("(allowed" in value for _, value in scan_text("Email hisabdo.app@gmail.com for support"))


def test_audit_sheet_records_every_required_field():
    rows = list(csv.DictReader((ROOT / "data" / "knowledge_source_audit.csv").open(encoding="utf-8-sig")))
    assert len(rows) >= 50 and len({r["source_id"] for r in rows}) == len(rows)
    for r in rows:
        for column in ("content_owner", "category", "url", "last_verified", "review_policy", "verdict"):
            assert r[column].strip(), f"{r['source_id']} has no {column}"


def test_new_or_corrected_kb_entries_cite_an_official_source():
    docs = json.loads((ROOT / "data" / "faq_docs.json").read_text(encoding="utf-8"))
    for d in docs:
        if "verified_on" in d:
            assert d.get("source", "").startswith("https://"), d["id"]
