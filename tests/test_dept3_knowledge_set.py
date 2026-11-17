"""Department 3 knowledge set: schema, purge, verified sample (docs/dept3-knowledge-set.md)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_dept3_knowledge_set as B  # noqa: E402

D = ROOT / "data" / "kb" / "dept3"


def load(name):
    return [json.loads(l) for l in (D / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def test_every_record_matches_the_schema():
    schema = json.loads(B.SCHEMA.read_text(encoding="utf-8"))
    records = load("knowledge_set.jsonl")
    assert len(records) == 363
    for r in records:
        assert B.validate(r, schema) == [], r["record_id"]


def test_ids_unique_every_module_assigned_and_no_promotional_filler():
    records = load("knowledge_set.jsonl")
    assert len({r["record_id"] for r in records}) == len(records)
    assert all(r["product_module"] in B.EXPENSE_MANAGEMENT_MODULES | set(B.MODULE_BY_AREA.values()) for r in records)
    assert not any(B.PROMO.search(r["content"]) for r in records)
    assert "off-04-016-start-managing-your-finances" not in {r["record_id"] for r in records}


def test_content_is_the_cleaned_source_text_unchanged():
    chunks = {c["id"]: c for c in (json.loads(l) for l in B.KB.read_text(encoding="utf-8").splitlines())}
    for r in load("knowledge_set.jsonl"):
        c = chunks[r["record_id"]]
        assert r["content"] == f"## {c['heading']}\n\n{c['body']}"   # no rewording, nothing added


def test_sample_batch_is_verified():
    v = json.loads((D / "sample_verification.json").read_text(encoding="utf-8"))
    assert v["sample_size"] == 28 and v["passed"] == 28
    assert {r["product_module"] for r in v["records"]} == set(B.MODULE_BY_AREA.values())


def test_validator_catches_bad_records():
    schema = json.loads(B.SCHEMA.read_text(encoding="utf-8"))
    good = load("sample_batch.jsonl")[0]
    assert B.validate({**good, "product_module": "crypto"}, schema)
    assert B.validate({**good, "source_url": "http://x"}, schema)
    assert B.validate({k: v for k, v in good.items() if k != "title"}, schema)
    assert B.validate({**good, "extra": 1}, schema)
