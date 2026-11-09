# Department 3 Knowledge Ingestion and Update Guide

## 1. Purpose
Standard process for maintaining Department 3 knowledge assets.

## 2. Knowledge Sources
| File | Records | Purpose |
|---|---:|---|
| data/faq_docs.json | 12 | FAQ retrieval |
| data/sample_financial_knowledge.json | 6 | Financial knowledge retrieval |
| data/structured_knowledge_chunks.json | 18 | Structured knowledge chunks |
| data/department3_verified_sample_batch.json | 18 | Verified sample batch |

## 3. Required Metadata
title, section, category, source_url, language, updated_date, product_area.

All required text fields must be nonempty. source_url must be HTTP or HTTPS, or null. updated_date must use YYYY-MM-DD, or null.

## 4. Current Categories
general, financial_concept, hisabdo.

## 5. Current Product Modules
HisabDo, HisabDo Privacy, General Financial Knowledge.

## 6. Content Preservation
Preserve original meaning. Remove unrelated navigation text and promotional filler only when present. Never invent features, URLs, dates, approvals, or product claims. Keep unknown URLs and dates null. Preserve records needed by separate retrieval workflows.

## 7. Ingestion Procedure
1. Confirm source authorization.
2. Review content accuracy and relevance.
3. Remove unrelated navigation and promotional text.
4. Preserve original meaning.
5. Assign a unique record ID.
6. Attach all required metadata.
7. Record only verified URLs and dates.
8. Validate JSON and metadata.
9. Run retrieval tests before publishing.

## 8. Update Procedure
1. Back up the source file.
2. Locate the record by ID.
3. Update verified content and metadata only.
4. Preserve retrieval specific fields.
5. Update structured chunks when source records change.
6. Run validation and retrieval tests.
7. Record update reason and review status.

## 9. Validation
Run metadata batch validation for all knowledge files. Every file must report zero errors. Review retrieval results after changes.

## 10. Verified Status
FAQ records: 12.
Financial knowledge records: 6.
Structured chunks: 18.
Unique chunk IDs: 18.
Missing required metadata: 0.
Verified sample records: 18.
Sample batch exact match: confirmed.
Sample batch validation errors: 0.

## 11. Outstanding Review
Source URLs, last updated dates, formal ownership, approval, and live product verification remain pending. Do not mark sources formally approved without evidence.
