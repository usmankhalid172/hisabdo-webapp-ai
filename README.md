# Automated Ingestion Pipeline & Error Logging Setup

**Owner:** Muhammad Daniyal

This is a focused submission package containing only the files relevant to the Automated Ingestion Pipeline & Error Logging Setup task. It is not a complete application repository.

## Contents
- `src/xictek_website_assistant/`: ingestion, chunking, TF-IDF embedding, configuration, and vector-store implementation.
- `src/logging_config.py`: shared application logger used by the vector store.
- `tests/xictek_website_assistant/`: focused regression tests.
- `docs/`: task report in Markdown and DOCX formats.

## Apply to the project
Extract this ZIP into the root of the existing `hisabdo-webapp-ai` repository and allow the included files to merge into their matching folders. The ZIP intentionally excludes the rest of the application, local virtual environments, caches, secrets, and generated index files.

## Run ingestion
From the full repository root, with project dependencies installed and outbound HTTPS access available:

```bash
python -m src.xictek_website_assistant.ingest
```

## Run focused tests
From the full repository root:

```bash
python -m pytest tests/xictek_website_assistant/test_ingest_dedup.py tests/xictek_website_assistant/test_ingestion_pipeline.py tests/xictek_website_assistant/test_chunking.py tests/xictek_website_assistant/test_vector_store.py tests/xictek_website_assistant/test_vector_store_mmr.py -q
```

The report documents the automated validation performed and explicitly distinguishes it from a fresh live crawl.
