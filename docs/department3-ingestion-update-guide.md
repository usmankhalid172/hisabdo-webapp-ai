# Department 3 — Knowledge Ingestion and Update Guide

## 1. Purpose

This guide defines a controlled process for preparing, validating,
and updating HisabDo product knowledge records.

## 2. Before Ingestion

1. Obtain the official source document or authorized reference.
2. Confirm the source owner and approval status.
3. Record the source URL and last-updated date when available.
4. Confirm the document language and relevant product module.
5. Do not treat repository drafts or sample data as approved product sources.

## 3. Content Cleaning

1. Preserve the original meaning and product-specific instructions.
2. Remove repeated navigation and footer text only after checking the source.
3. Remove promotional filler only when confirmed unrelated to product usage.
4. Check possible duplicates before removing or merging records.
5. Preserve warnings, limitations, conditions, and important examples.
6. Do not invent missing features, UI steps, URLs, or instructions.

## 4. Metadata Preparation

For every record, maintain:

- title
- section
- category
- source_url
- language
- last_updated
- product_module

Retain compatibility fields:

- id
- text
- product_area
- source_verification

Use null for unavailable source URLs and update dates.
Keep verification pending until the source has been reviewed.
Keep provisional module mappings clearly identified.

## 5. Validation Before Ingestion

1. Validate JSON syntax and ensure the root is a list.
2. Check that every record has a unique ID.
3. Confirm original IDs and content are preserved unless an approved edit exists.
4. Check required metadata fields and allowed null values.
5. Check product module classifications against approved source material.
6. Review possible duplicate or conflicting records.
7. Run relevant retrieval and knowledge-base tests.
8. Review the final diff before committing.

## 6. Update and Backup Procedure

1. Keep an unchanged backup of the current knowledge source.
2. Prepare updates in a separate staging file.
3. Compare staging records with the original.
4. Obtain source-owner review for content or classification changes.
5. Update the active knowledge source only after compatibility checks and approval.
6. Update the knowledge-base manifest if the approved ingestion process requires it.
7. Record the change date, source, and review status.

## 7. Privacy and Security

- Use only authorized product documentation and approved reference materials.
- Do not add real customer financial records, credentials, tokens, or personal data.
- Do not include secrets in logs or test fixtures.
- Keep test data separate from production data.

## 8. Current Department 3 Status

- Staging dataset: data/department3_staging_knowledge.json
- Records structurally validated: 16
- Metadata schema: docs/department3-metadata-schema.md
- Source approval: pending
- Source URL and last-updated verification: pending
- Product module mapping: provisional
- Active knowledge source: unchanged

The current staging dataset must not be treated as production-approved
until source-owner verification and required reviews are complete.
