import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    "data/faq_docs.json",
    "data/sample_financial_knowledge.json",
]
OUTPUT = ROOT / "data/structured_knowledge_chunks.json"
MANIFEST = ROOT / "data/department3_ingestion_manifest.json"
REPORT = ROOT / "docs/department3_automated_ingestion_execution_report.md"

CONFIG = {
    "chunking_unit": "characters",
    "faq": {"strategy": "one_complete_record", "max_size": 0, "overlap": 0},
    "financial_concept": {
        "strategy": "question_answer_keywords_together",
        "max_size": 0,
        "overlap": 0,
    },
    "feature_table": {
        "strategy": "header_and_related_rows",
        "max_size": 1000,
        "overlap": 0,
    },
    "workflow_guidelines": {
        "strategy": "paragraph_boundary",
        "max_size": 1000,
        "overlap": 120,
    },
    "long_documentation": {
        "strategy": "heading_and_paragraph_boundary",
        "max_size": 1500,
        "overlap": 180,
    },
    "current_retrieval": {
        "vectorizer": "sklearn.feature_extraction.text.TfidfVectorizer",
        "scikit_learn_version": "1.5.2",
        "stop_words": "english",
        "similarity": "cosine",
        "relevance_threshold": 0.30,
        "neural_embedding_model": None,
        "external_vector_index": None,
    },
}


def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def content_of(record, source):
    if source.endswith("faq_docs.json"):
        return record.get("text", "").strip()

    question = record.get("question", "").strip()
    answer = record.get("answer", "").strip()
    keywords = record.get("keywords", [])
    if not isinstance(keywords, list):
        raise ValueError("Financial keywords must be a list")
    return "\n".join(
        part for part in [
            f"Question: {question}" if question else "",
            f"Answer: {answer}" if answer else "",
            "Keywords: " + ", ".join(str(x) for x in keywords) if keywords else "",
        ] if part
    )


def split_long_text(text, max_size, overlap):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_size:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(paragraph):
                end = min(start + max_size, len(paragraph))
                chunks.append(paragraph[start:end])
                if end == len(paragraph):
                    break
                start = max(start + 1, end - overlap)
            continue

        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            carry = current[-overlap:] if current and overlap else ""
            current = f"{carry}\n\n{paragraph}".strip()

    if current:
        chunks.append(current)
    return chunks


def main():
    started = datetime.now(timezone.utc).isoformat()
    old_manifest = {}
    if MANIFEST.exists():
        try:
            old_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            old_manifest = {}

    previous = old_manifest.get("records", {})
    previous_chunks = (
        json.loads(OUTPUT.read_text(encoding="utf-8"))
        if OUTPUT.exists() else []
    )
    current = {}
    output_chunks = []
    errors = []
    failed_sources = []
    duplicate_ids = []
    duplicate_content = []
    seen_content = set()
    source_counts = {}

    for source in SOURCES:
        path = ROOT / source
        if not path.exists():
            failed_sources.append(source)
            errors.append(f"{source}: source file not found")
            continue

        try:
            records = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise ValueError("Source JSON must contain a list")
        except Exception as exc:
            failed_sources.append(source)
            errors.append(f"{source}: JSON parsing failed: {exc}")
            continue

        source_counts[source] = len(records)
        seen_ids = set()

        for index, record in enumerate(records):
            try:
                if not isinstance(record, dict):
                    raise ValueError("Record must be an object")

                record_id = record.get("id")
                if not isinstance(record_id, str) or not record_id.strip():
                    raise ValueError("Missing record ID")
                if record_id in seen_ids:
                    duplicate_ids.append(f"{source}:{record_id}")
                    raise ValueError(f"Duplicate ID within source: {record_id}")
                seen_ids.add(record_id)

                title = record.get("title")
                if not isinstance(title, str) or not title.strip():
                    raise ValueError("Missing title")

                text = content_of(record, source)
                if not text.strip():
                    raise ValueError("Missing usable content")

                key = f"{source}:{record_id}"
                record_hash = digest(record)
                current[key] = record_hash

                normalized = re.sub(r"\s+", " ", text).strip().casefold()
                content_key = (source, normalized)
                if content_key in seen_content:
                    duplicate_content.append(key)
                seen_content.add(content_key)

                category = record.get("category", "")
                if source.endswith("faq_docs.json"):
                    pieces = [text]
                else:
                    pieces = [text]

                for chunk_index, piece in enumerate(pieces, start=1):
                    output_chunks.append({
                        "chunk_id": (
                            f"{Path(source).stem}:{record_id}:"
                            f"chunk-{chunk_index:03d}"
                        ),
                        "chunk_index": chunk_index,
                        "document_id": record_id,
                        "title": title,
                        "section": record.get("section", ""),
                        "category": category,
                        "text": piece,
                        "source_url": record.get("source_url"),
                        "language": record.get("language", "en"),
                        "updated_date": record.get("updated_date"),
                        "product_area": record.get("product_area", ""),
                        "source_file": source,
                    })
            except Exception as exc:
                errors.append(f"{source}, record {index + 1}: {exc}")

    # Preserve the last known good data for any source that failed to load.
    for source in failed_sources:
        prefix = source + ":"
        for key, value in previous.items():
            if key.startswith(prefix):
                current.setdefault(key, value)

    if failed_sources:
        retained_chunks = [
            chunk for chunk in previous_chunks
            if chunk.get("source_file") in failed_sources
        ]
        retained_ids = {chunk.get("chunk_id") for chunk in retained_chunks}
        output_chunks = retained_chunks + [
            chunk for chunk in output_chunks
            if chunk.get("chunk_id") not in retained_ids
        ]

    added = sorted(set(current) - set(previous))
    deleted = sorted(set(previous) - set(current))
    modified = sorted(
        key for key in set(current) & set(previous)
        if current[key] != previous[key]
    )
    unchanged = len(set(current) & set(previous)) - len(modified)

    OUTPUT.write_text(
        json.dumps(output_chunks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps({
            "generated_at": started,
            "records": current,
            "sources": SOURCES,
            "configuration": CONFIG,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    status = "PASS" if not errors and not failed_sources else "REVIEW REQUIRED"
    report = [
        "# Department 3 Automated Ingestion Execution Report",
        "",
        f"Execution time: {started}",
        f"Status: {status}",
        "",
        "## Source results",
        "",
        "| Source | Records read |",
        "|---|---:|",
    ]
    report.extend(f"| {name} | {count} |" for name, count in source_counts.items())
    report.extend([
        "",
        "## Change detection",
        "",
        f"New records: {len(added)}",
        f"Modified records: {len(modified)}",
        f"Deleted records: {len(deleted)}",
        f"Unchanged records: {unchanged}",
        f"Generated chunks: {len(output_chunks)}",
        f"Duplicate IDs: {len(duplicate_ids)}",
        f"Duplicate content within source: {len(duplicate_content)}",
        f"Failed source files: {len(failed_sources)}",
        f"Parsing and record errors: {len(errors)}",
        "",
        "## Errors and duplicates",
        "",
    ])
    report.extend(f"* {item}" for item in errors + duplicate_ids + duplicate_content)
    if not errors and not duplicate_ids and not duplicate_content:
        report.append("No errors or duplicates detected.")

    report.extend([
        "",
        "## Reproducibility configuration",
        "",
        "```json",
        json.dumps(CONFIG, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Scope and limitations",
        "",
        "Sources currently include local JSON files only. Remote web pages are not fetched.",
        "The current retrieval implementation uses TF IDF, not a neural embedding model.",
        "No external vector database or persistent vector index is configured.",
        "The manifest records content hashes for repeatable change detection.",
        "A deleted source file is reported as a failed source, not treated as an empty source.",
        "Chunk output is regenerated from successfully parsed records. Review errors before publishing.",
        "",
    ])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("Ingestion status:", status)
    print("Sources read:", len(source_counts))
    print("Records:", len(current))
    print("Chunks generated:", len(output_chunks))
    print("New:", len(added), "Modified:", len(modified), "Deleted:", len(deleted))
    print("Duplicate IDs:", len(duplicate_ids))
    print("Duplicate content:", len(duplicate_content))
    print("Failed sources:", len(failed_sources))
    print("Errors:", len(errors))
    print("Output:", OUTPUT.relative_to(ROOT))
    print("Manifest:", MANIFEST.relative_to(ROOT))
    print("Report:", REPORT.relative_to(ROOT))


if __name__ == "__main__":
    main()
