import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "department3_ingest.py"

def run_ingestion(tmp_path, records):
    source = tmp_path / "source.json"
    manifest = tmp_path / "manifest.json"
    output = tmp_path / "chunks.json"
    report = tmp_path / "report.json"
    source.write_text(json.dumps(records), encoding="utf-8")

    subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--source", str(source),
            "--manifest", str(manifest),
            "--output", str(output),
            "--report", str(report),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return (
        json.loads(manifest.read_text(encoding="utf-8")),
        json.loads(output.read_text(encoding="utf-8")),
        json.loads(report.read_text(encoding="utf-8")),
    )

def sample(record_id="faq-001", text="HisabDo tracks expenses"):
    return {
        "id": record_id,
        "title": "What is HisabDo?",
        "text": text,
        "product_module": "HisabDo",
    }

def test_first_run_tracks_new_records(tmp_path):
    manifest, chunks, report = run_ingestion(tmp_path, [sample()])
    assert report["changes"]["added"] == ["faq-001"]
    assert len(chunks) == 1
    assert manifest["record_count"] == 1

def test_second_run_tracks_unchanged_records(tmp_path):
    records = [sample()]
    run_ingestion(tmp_path, records)
    _, _, report = run_ingestion(tmp_path, records)
    assert report["changes"]["unchanged"] == ["faq-001"]

def test_modified_record_is_detected(tmp_path):
    run_ingestion(tmp_path, [sample()])
    _, _, report = run_ingestion(tmp_path, [sample(text="Updated expense tracking")])
    assert report["changes"]["modified"] == ["faq-001"]

def test_deleted_record_is_detected(tmp_path):
    run_ingestion(tmp_path, [sample()])
    _, _, report = run_ingestion(tmp_path, [])
    assert report["changes"]["deleted"] == ["faq-001"]

def test_duplicate_ids_are_reported(tmp_path):
    _, _, report = run_ingestion(tmp_path, [sample(), sample()])
    assert report["duplicate_ids"] == ["faq-001"]

def test_duplicate_content_is_reported(tmp_path):
    first = sample("faq-001")
    second = sample("faq-002")
    _, _, report = run_ingestion(tmp_path, [first, second])
    assert report["duplicate_content_record_ids"] == ["faq-002"]

def test_malformed_record_is_reported(tmp_path):
    _, _, report = run_ingestion(tmp_path, [sample(), {"id": "bad"}])
    assert any(item.get("id") == "bad" for item in report["validation_errors"])

def test_invalid_embedding_is_reported(tmp_path):
    record = sample()
    record["embedding"] = ["not-a-number"]
    _, _, report = run_ingestion(tmp_path, [record])
    assert report["vector_parsing_errors"][0]["id"] == "faq-001"

def test_long_document_is_chunked(tmp_path):
    record = sample(text=" ".join(["expense"] * 600))
    record["content_type"] = "documentation"
    _, chunks, _ = run_ingestion(tmp_path, [record])
    assert len(chunks) == 2

def test_source_data_is_not_modified(tmp_path):
    record = sample()
    original = json.dumps([record])
    source = tmp_path / "source.json"
    source.write_text(original, encoding="utf-8")
    run_ingestion(tmp_path, [record])
    assert source.read_text(encoding="utf-8") == original
