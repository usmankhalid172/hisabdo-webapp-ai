# Department 3 — Knowledge Metadata Schema

## 1. Purpose

This schema standardizes metadata for HisabDo product knowledge records.
It is designed to preserve source meaning and maintain compatibility
with existing knowledge-base consumers.

## 2. Required Metadata Fields

| Field | Type | Rule |
|---|---|---|
| title | string | Required; preserve source title |
| section | string | Required; preserve existing section |
| category | string | Required; preserve existing category |
| source_url | string or null | Official source URL; null until verified |
| language | string | Required; use a confirmed language code |
| last_updated | string or null | Source update date in YYYY-MM-DD format; null if unknown |
| product_module | string | Required; module classification; provisional until approved |

## 3. Existing Compatibility Fields

| Field | Purpose |
|---|---|
| id | Stable record identifier; never change without approval |
| text | Original knowledge content; preserve meaning |
| product_area | Existing field retained for compatibility |
| source_verification | Verification status; pending until evidence and approval exist |

## 4. Verification Rules

- Do not invent source URLs, dates, owners, or approvals.
- Use null when source URL or update date is unavailable.
- Keep source_verification as pending until the source is checked.
- Do not describe pending content as officially approved or verified.
- Do not merge conflicting or overlapping content without source-owner review.
- Keep product_module aligned with product_area only as a provisional mapping.
- Preserve original IDs, titles, and text during metadata-only updates.

## 5. Content Cleaning Rules

- Remove repeated navigation, footer, or promotional text only when it is confirmed to be unrelated to the product documentation.
- Remove duplicate content only after confirming that the records are genuinely redundant.
- Preserve product instructions, conditions, limitations, and warnings.
- Never add unsupported product features or UI steps.
- Record substantive edits for review.

## 6. Current Staging Status

- Staging source: data/faq_docs.json
- Staging output: data/department3_staging_knowledge.json
- Current records: 16
- Structural preservation validation: passed
- Source URLs and update dates: pending
- Source-owner approval: pending
- Product module mapping: provisional

This staging dataset is structurally validated, not source-approved.
