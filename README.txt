Submission: Knowledge Base Ingestion & Update Technical Specification
Prepared by: Muhammad Daniyal
Date: 9 November 2026

Files:
1. Knowledge_Base_Ingestion_Update_Technical_Specification.docx — formatted handover document.
2. Knowledge_Base_Ingestion_Update_Technical_Specification.md — editable Markdown source.
3. metadata_validator.py — standalone reference validator for JSONL, JSON, and CSV metadata.
4. README.txt — package notes and usage.

Validator usage (from a terminal):
    python metadata_validator.py path/to/records.jsonl
    python metadata_validator.py path/to/records.json
    python metadata_validator.py path/to/records.csv

The validator uses the proposed initial allow-lists in the specification. Product
owners/team leads must approve the final domains and product-tag taxonomy before
production use. It is a standalone reference companion and is not integrated
into the repository's live ingest pipeline.

The specification was grounded in a review of the supplied repository archive:
src/xictek_website_assistant/ingest.py, chunking.py, vector_store.py,
config.py, schemas.py, and data/xictek_faq_raw.jsonl / data/index/chunks.json.

It documents current behavior separately from proposed standards. It does not
claim that the proposed schema, validators, or update workflow have been
deployed or that a production ingestion run was performed.
