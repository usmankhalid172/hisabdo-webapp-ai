import json
from pathlib import Path

path = Path("data/faq_docs.json")
data = json.loads(path.read_text(encoding="utf-8"))

if not isinstance(data, list):
    raise ValueError("Expected a JSON list in data/faq_docs.json")

by_id = {item.get("id"): item for item in data}
today = "2026-10-13"

official_product_source = (
    "Official HisabDo FAQ — https://hisabdo.app/faq"
)
finance_source = (
    "OpenStax, Principles of Financial Accounting, Section 2.1 — "
    "https://openstax.org/books/principles-financial-accounting/"
    "pages/2-1-describe-the-income-statement-statement-of-owners-equity-"
    "balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate"
)

# Verify only basic accounting concepts supported by the reference.
finance_ids = {
    "faq-004",
    "faq-006",
    "finance_001",
    "finance_002",
    "finance_003",
    "finance_004",
    "finance_007",
    "finance_008",
}

updated = []

for doc_id in finance_ids:
    item = by_id.get(doc_id)
    if item:
        item["source"] = finance_source
        item["verified"] = True
        item["last_reviewed"] = today
        item["version"] = "1.1.0"
        updated.append(doc_id)

# Replace product claims with statements supported by official documentation.
item = by_id.get("faq-001")
if item:
    item["text"] = (
        "HisabDo is an offline-first khata and ledger app for Android. "
        "It helps users track money given and received, customer balances, "
        "and expenses. PDF reports are available for supported records."
    )
    item["source"] = official_product_source
    item["verified"] = True
    item["last_reviewed"] = today
    item["version"] = "1.2.0"
    updated.append("faq-001")

safe_report_text = (
    "HisabDo supports PDF reports for supported records. Official "
    "documentation describes reports for transactions, customer balances, "
    "and customer activity. The exact steps may depend on the screen and "
    "record being viewed. CSV export is not confirmed by the source."
)

for doc_id in ("faq-005", "product_001"):
    item = by_id.get(doc_id)
    if item:
        item["text"] = safe_report_text
        item["source"] = official_product_source
        item["verified"] = True
        item["last_reviewed"] = today
        item["version"] = "1.1.0"
        updated.append(doc_id)

# Explicitly keep sensitive or implementation-specific claims unverified.
for doc_id in ("faq-002", "faq-003", "product_002", "product_003"):
    item = by_id.get(doc_id)
    if item:
        item["verified"] = False

path.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("Knowledge base updated.")
print("Updated entries:", ", ".join(updated) if updated else "none")
print("Unverified product/implementation claims were kept unverified.")
print("Total documents:", len(data))
print("Verified documents:", sum(x.get("verified") is True for x in data))
