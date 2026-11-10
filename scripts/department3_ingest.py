import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)

def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def classify(record):
    kind = str(record.get("content_type", "")).lower()
    if kind in {"faq", "table", "workflow", "documentation"}:
        return kind
    if str(record.get("id", "")).startswith("faq-"):
        return "faq"
    return "documentation"

def make_chunks(record):
    title = str(record.get("title", "")).strip()
    body = str(record.get("text", "")).strip()
    kind = classify(record)
    if not title or not body:
        raise ValueError("Missing title or text")

    content = f"Title: {title}\n\n{body}"

    if kind in {"faq", "table", "workflow"}:
        return [{"text": content, "chunk_index": 0, "content_type": kind}]

    words = content.split()
    target, overlap = 450, 75
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + target, len(words))
        chunks.append({
            "text": " ".join(words[start:end]),
            "chunk_index": len(chunks),
            "content_type": kind
        })
        if end == len(words):
            break
        start = end - overlap
    return chunks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/department3_staging_knowledge.json")
    parser.add_argument("--manifest", default="data/department3_ingestion_manifest.json")
    parser.add_argument("--output", default="data/department3_ingested_chunks.json")
    parser.add_argument("--report", default="docs/department3-ingestion-execution-report.json")
    args = parser.parse_args()

    source_path = ROOT / args.source
    manifest_path = ROOT / args.manifest
    output_path = ROOT / args.output
    report_path = ROOT / args.report

    timestamp = datetime.now(timezone.utc).isoformat()
    errors, duplicate_ids, duplicate_content = [], [], []
    failed_pages, vector_errors, unresolved_sources = [], [], []
    records_by_id = {}
    content_seen = set()
    chunks = []

    try:
        records = read_json(source_path)
    except Exception as exc:
        raise SystemExit(f"Cannot read source JSON: {exc}")

    if not isinstance(records, list):
        raise SystemExit("Source JSON must contain a list")

    previous = {}
    if manifest_path.exists():
        try:
            previous = read_json(manifest_path).get("records", {})
        except Exception as exc:
            raise SystemExit(f"Cannot read previous manifest: {exc}")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append({"record_index": index, "error": "Record is not an object"})
            continue

        record_id = str(record.get("id", "")).strip()
        if not record_id:
            errors.append({"record_index": index, "error": "Missing record ID"})
            continue
        if record_id in records_by_id:
            duplicate_ids.append(record_id)
            continue

        if not str(record.get("title", "")).strip() or not str(record.get("text", "")).strip():
            errors.append({"id": record_id, "error": "Missing title or text"})
            continue

        content_hash = digest(record)
        records_by_id[record_id] = content_hash

        normalized_text = " ".join(str(record["text"]).lower().split())
        text_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        if text_hash in content_seen:
            duplicate_content.append(record_id)
        content_seen.add(text_hash)

        if not record.get("source_url"):
            unresolved_sources.append(record_id)

        try:
            record_chunks = make_chunks(record)
            for chunk in record_chunks:
                chunk["record_id"] = record_id
                chunk["title"] = record["title"]
                chunk["product_module"] = record.get("product_module")
                chunk["source_url"] = record.get("source_url")
                chunk["content_hash"] = content_hash
                chunks.append(chunk)
        except Exception as exc:
            errors.append({"id": record_id, "error": str(exc)})

        embedding = record.get("embedding")
        if embedding is not None:
            try:
                if not isinstance(embedding, list) or not embedding:
                    raise ValueError("Embedding must be a non-empty list")
                if not all(isinstance(v, (int, float)) for v in embedding):
                    raise ValueError("Embedding contains non-numeric values")
            except Exception as exc:
                vector_errors.append({"id": record_id, "error": str(exc)})

    added = sorted(set(records_by_id) - set(previous))
    deleted = sorted(set(previous) - set(records_by_id))
    modified = sorted(
        record_id for record_id in set(records_by_id) & set(previous)
        if records_by_id[record_id] != previous[record_id]
    )
    unchanged = sorted(
        record_id for record_id in set(records_by_id) & set(previous)
        if records_by_id[record_id] == previous[record_id]
    )

    manifest = {
        "manifest_version": "1.0",
        "generated_at": timestamp,
        "source_file": args.source,
        "record_count": len(records_by_id),
        "records": records_by_id,
        "chunk_count": len(chunks),
        "embedding_status": "not_generated_by_this_pipeline"
    }

    report = {
        "generated_at": timestamp,
        "source_file": args.source,
        "input_record_count": len(records),
        "valid_record_count": len(records_by_id),
        "chunk_count": len(chunks),
        "changes": {
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "unchanged": unchanged
        },
        "duplicate_ids": duplicate_ids,
        "duplicate_content_record_ids": duplicate_content,
        "validation_errors": errors,
        "failed_pages": failed_pages,
        "unresolved_source_urls": unresolved_sources,
        "vector_parsing_errors": vector_errors,
        "embedding_generated": False,
        "notes": [
            "No source URLs were fetched by this offline staging pipeline.",
            "Records without source URLs require source-owner verification.",
            "No production embeddings or vector index were generated."
        ]
    }

    write_json(output_path, chunks)
    write_json(manifest_path, manifest)
    write_json(report_path, report)

    print("Ingestion completed.")
    print(f"Records: {len(records_by_id)}")
    print(f"Chunks: {len(chunks)}")
    print(f"Added: {len(added)} | Modified: {len(modified)} | Deleted: {len(deleted)}")
    print(f"Duplicate IDs: {len(duplicate_ids)}")
    print(f"Duplicate content: {len(duplicate_content)}")
    print(f"Validation errors: {len(errors)}")
    print(f"Vector parsing errors: {len(vector_errors)}")
    print(f"Unresolved source URLs: {len(unresolved_sources)}")
    print(f"Report: {report_path}")

if __name__ == "__main__":
    main()
