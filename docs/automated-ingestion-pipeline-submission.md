# Automated Ingestion Pipeline & Error Logging Setup

**Owner:** Muhammad Daniyal  
**Project:** XICTEK Website Assistant / HisabDo AI repository  
**Task:** Automated Ingestion Pipeline & Error Logging Setup

## Objective

Provide a repeatable website knowledge-ingestion process that records page-fetch and extraction failures, detects content changes, checks duplicate/invalid vectors, and produces auditable run artifacts.

## Implementation delivered

### 1. Crawl and extraction monitoring

- Keeps the existing allow-listed, same-domain breadth-first crawl.
- Normalizes URLs by removing fragments, lower-casing scheme/host, and removing default ports.
- Records successful HTML pages, non-HTML skips, HTTP/network failures, empty extraction results, and parser/extraction exceptions.
- Isolates a page-level failure so one bad URL does not terminate the entire crawl.

### 2. Structured error and run logging

Each run writes JSON Lines events to:

`src/xictek_website_assistant/data/ingestion_logs/ingestion_<UTC-run-id>.jsonl`

Events include timestamps, severity, event name, URL, HTTP status/content type where applicable, exception type/message, and run summary fields.

### 3. New, updated, unchanged and removed source tracking

- Computes a SHA-256 digest of normalized extracted page text.
- Compares the current crawl with `data/source_manifest.json`.
- Reports new, updated and unchanged URLs.
- Reports removed URLs only when the scan is complete and has no fetch or parse failures.
- Does not replace the prior manifest after a partial/failed scan, preventing temporary outages from being misreported as deleted sources.

### 4. Duplicate and vector integrity checks

- Retains existing per-page exact chunk deduplication.
- Detects repeated chunk text across source pages without globally deleting it, preserving source attribution.
- Detects exact duplicate embedding rows using SHA-256 hashes of vector bytes.
- Counts zero vectors and rejects non-finite embedding values or chunk/vector row mismatches before index persistence.

### 5. Index persistence and metadata

- Writes UTF-8 JSON explicitly, preventing Windows code-page serialization failures.
- Writes temporary index files before replacing persisted files.
- Records the actual backend (`scikit-learn TfidfVectorizer`), embedding identifier, matrix shape, chunk count and dtype in `metadata.json`.
- Validates persisted chunk/vector dimensions and finite values when loading an index.
- Corrects stale documentation and metadata that previously described Sentence Transformers although the runtime code uses TF-IDF.

## Generated run artifacts

After running the ingestion command, the following artifacts are created under `src/xictek_website_assistant/data/`:

- `ingestion_logs/` — per-run JSONL event logs.
- `ingestion_report.json` — machine-readable summary including crawl failures, source changes, duplicate text/vector counts, zero vectors, matrix dimensions and duration.
- `source_manifest.json` — last successfully completed source snapshot.
- `index/` — chunks, vectors, metadata and fitted TF-IDF vectorizer.

## How to run

From the repository root:

```bash
python -m src.xictek_website_assistant.ingest
```

The command requires outbound HTTPS access to the configured XICTEK and HisabDo domains. Run it from a developer machine or CI runner with network access. A partial crawl can rebuild the index from pages that were successfully extracted, but it will not commit source removals to the manifest.

## Validation performed on the supplied repository archive

- Python compilation: **passed** (`compileall` for the XICTEK assistant package and its tests).
- Focused automated tests: **29 passed** across ingestion deduplication, new pipeline diagnostics, chunking, vector-store persistence/query behavior and MMR.
- Default embedding-backend configuration test: **passed**.
- Existing checked-in index audit: **976 chunks**, **976 embedding rows**, matrix shape **976 × 2,109**, **115 source URLs**, no empty chunks, no exact duplicate chunk texts, no exact duplicate vector rows and no zero vectors.
- The checked-in index metadata was corrected to identify the actual TF-IDF backend.

**Execution limitation:** a fresh live website crawl was not run in this package-validation environment. The ingestion command is ready for a network-enabled run; its report and JSONL logs will provide the live evidence after execution. This submission does not claim that a new live crawl was performed during packaging.

## Important technical limitation

The repository's current embedding implementation is TF-IDF (lexical word/bigram matching), not a multilingual semantic Sentence Transformers model. The metadata and documentation now state this accurately. The embedding feature dimension is corpus-dependent. Cross-language retrieval quality is therefore not guaranteed by the multilingual response prompt.

## Acceptance summary

The code now provides repeatable ingestion, per-page failure isolation, structured event logs, source-change classification with safe deletion semantics, duplicate text/vector diagnostics, vector integrity validation and machine-readable run reports. The live crawl and resulting run artifacts should be generated on the network-enabled development machine before release sign-off.
