"""Build the standardized Department 3 knowledge set from the approved KB and verify a sample batch.

Input : data/kb/approved/kb_chunks.jsonl (cleaned chunks; see docs/kb-content-cleaning.md)
        data/kb/sources/<date>/<source_id>.html (the source snapshots, for the meaning check)
Output: data/kb/dept3/knowledge_set.jsonl          every record, schema v1.0
        data/kb/dept3/purge_report.json            what was removed and why
        data/kb/dept3/sample_batch.jsonl           stratified sample (2 per product module)
        data/kb/dept3/sample_verification.json     per-record checks on the sample
Schema: data/kb/dept3/schema/knowledge_record.schema.json

    python scripts/build_dept3_knowledge_set.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from clean_knowledge_sources import unsupported_sentences, words  # noqa: E402
from clean_product_faqs import clean_text  # noqa: E402

KB = ROOT / "data" / "kb" / "approved" / "kb_chunks.jsonl"
SNAPSHOTS = ROOT / "data" / "kb" / "sources"
OUT = ROOT / "data" / "kb" / "dept3"
SCHEMA = OUT / "schema" / "knowledge_record.schema.json"
SCHEMA_VERSION = "1.0"

# area (assigned at cleaning time from the chunk's words) -> product module of the HisabDo app
MODULE_BY_AREA = {
    "Expenses & Income": "expenses_income", "Customers & Receivables": "customers_udhar",
    "Suppliers & Payables": "suppliers_payables", "Khata & Ledger": "khata_ledger",
    "Reports & PDF Export": "reports_pdf", "Analytics": "reports_pdf", "Voice Entry": "entry_voice",
    "Data, Backup & Sync": "data_backup_sync", "Privacy & Security": "privacy_security",
    "Platform & Devices": "app_platform", "Pricing & Download": "app_platform",
    "Language & Currency": "language_currency", "Product Overview": "product_overview",
    "Company": "company_support", "Support": "company_support", "Legal & Policy": "legal_policy",
    "Business finance (general)": "general_bookkeeping",
}
EXPENSE_MANAGEMENT_MODULES = {"expenses_income", "customers_udhar", "suppliers_payables", "khata_ledger",
                              "reports_pdf", "entry_voice", "general_bookkeeping"}
DOC_TYPE = {"product_faq": "feature_faq", "product_guide": "product_documentation",
            "finance_guide": "workflow_guide", "legal_policy": "authorized_reference"}

# Promotional filler: a record whose heading or text is a call to action, not information.
PROMO = re.compile(r"\bdownload hisabdo today\b|\bsmart accounting, simplified\b|^start managing your finances$", re.I)


def module_of(c: dict) -> str:
    area = c["area"].replace(" (general practice)", "")
    return MODULE_BY_AREA.get(area, "general_bookkeeping")


def to_record(c: dict) -> dict:
    content = f"## {c['heading']}\n\n{c['body']}"
    module = module_of(c)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": c["id"],
        "title": c["title"],
        "section": c["section"],
        "heading": c["heading"],
        "category": c["category"],
        "doc_type": DOC_TYPE[c["category"]],
        "product_module": module,
        "expense_management_scope": module in EXPENSE_MANAGEMENT_MODULES,
        "scope": c["scope"],
        "source_id": c["source_id"],
        "source_url": c["source_url"],
        "language": c["language"],
        "last_updated": c["last_updated"],
        "last_updated_basis": c["last_updated_basis"],
        "retrieved_on": c["retrieved_on"],
        "next_review_due": c["next_review_due"],
        "review_policy": c["review_policy"],
        "owner": c["owner"],
        "approval": c["approval"],
        "usage": c["usage"],
        "status": c["status"],
        "notes": c.get("notes") or [],
        "content": content,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


# ------------------------------------------------------------------------------------ schema validation (no dependency)

def validate(record: dict, schema: dict) -> list[str]:
    errors = [f"missing:{k}" for k in schema["required"] if k not in record]
    errors += [f"unknown:{k}" for k in record if k not in schema["properties"]]
    for k, rule in schema["properties"].items():
        if k not in record:
            continue
        v, types = record[k], rule["type"] if isinstance(rule["type"], list) else [rule["type"]]
        pytypes = {"string": str, "boolean": bool, "array": list, "null": type(None)}
        if not any(isinstance(v, pytypes[t]) for t in types):
            errors.append(f"type:{k}")
            continue
        if isinstance(v, str):
            if "enum" in rule and v not in rule["enum"]:
                errors.append(f"enum:{k}={v}")
            if "pattern" in rule and not re.fullmatch(rule["pattern"], v):
                errors.append(f"pattern:{k}={v[:40]}")
            if "minLength" in rule and len(v) < rule["minLength"]:
                errors.append(f"minLength:{k}")
    return errors


# ------------------------------------------------------------------------------------ sample verification

def latest_snapshots() -> Path:
    return sorted(d for d in SNAPSHOTS.iterdir() if d.is_dir())[-1]


def page_words(source_id: str, snap: Path) -> str:
    html = (snap / f"{source_id}.html").read_text(encoding="utf-8")
    return words(clean_text(BeautifulSoup(html, "html.parser").get_text(" ")))


def verify_sample(sample: list[dict], schema: dict) -> list[dict]:
    snap, cache, out = latest_snapshots(), {}, []
    rewrites = {"this website", "hisabdo.app", "privacy policy", "contact page", "/blog/"}   # documented link rewrites
    for r in sample:
        if r["source_id"] not in cache:
            cache[r["source_id"]] = page_words(r["source_id"], snap)
        body = r["content"].split("\n\n", 1)[1]
        unsupported = [s for s in unsupported_sentences(body, cache[r["source_id"]])
                       if not any(w in s.lower() for w in rewrites)]
        checks = {
            "schema_valid": not validate(r, schema),
            "hash_matches_content": hashlib.sha256(r["content"].encode()).hexdigest() == r["content_sha256"],
            "every_sentence_on_source_page": not unsupported,
            "source_url_https": r["source_url"].startswith("https://"),
            "no_promotional_filler": not PROMO.search(r["heading"]) and not PROMO.search(body),
            "module_assigned": bool(r["product_module"]),
        }
        out.append({"record_id": r["record_id"], "product_module": r["product_module"], "checks": checks,
                    "passed": all(checks.values()), "unsupported_sentences": unsupported})
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    chunks = [json.loads(line) for line in KB.read_text(encoding="utf-8").splitlines() if line.strip()]
    records, purged = [], []
    for c in chunks:
        if PROMO.search(c["heading"]) or PROMO.search(c["body"]):
            purged.append({"record_id": c["id"], "reason": "promotional_filler", "heading": c["heading"]})
            continue
        records.append(to_record(c))
    # Exact duplicates across sources (same content hash) - the first, most authoritative copy is kept.
    seen, unique = {}, []
    for r in records:
        h = hashlib.sha256(r["content"].split("\n\n", 1)[1].encode()).hexdigest()
        if h in seen:
            purged.append({"record_id": r["record_id"], "reason": "duplicate", "duplicate_of": seen[h]})
            continue
        seen[h] = r["record_id"]
        unique.append(r)
    errors = {r["record_id"]: e for r in unique if (e := validate(r, schema))}
    if errors:
        print("SCHEMA ERRORS", errors)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "knowledge_set.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in unique:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    by_module = {}
    for r in unique:
        by_module.setdefault(r["product_module"], []).append(r)
    sample = [r for m in sorted(by_module) for r in by_module[m][:2]]
    with (OUT / "sample_batch.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in sample:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ver = verify_sample(sample, schema)
    report = {"schema_version": SCHEMA_VERSION, "records": len(unique), "input_chunks": len(chunks),
              "purged": purged, "by_module": dict(Counter(r["product_module"] for r in unique).most_common()),
              "expense_management_scope": sum(r["expense_management_scope"] for r in unique),
              "by_doc_type": dict(Counter(r["doc_type"] for r in unique)),
              "earlier_cleaning": "UI navigation, footers, CTAs, bylines, author boxes, related-article lists, stale "
                                  "counters and 2 duplicates were removed when the KB was cleaned "
                                  "(data/kb/approved/cleaning_report.json: 286 blocks)"}
    (OUT / "purge_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "sample_verification.json").write_text(json.dumps(
        {"sample_size": len(sample), "passed": sum(v["passed"] for v in ver), "records": ver}, indent=1,
        ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(unique)} records ({report['expense_management_scope']} expense-management) from {len(chunks)} chunks; "
          f"purged {len(purged)}; sample {sum(v['passed'] for v in ver)}/{len(sample)} verified")
    print(report["by_module"])
    for v in ver:
        if not v["passed"]:
            print("FAILED", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
