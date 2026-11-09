# Cleanup and Validation Report

## Scope
Input: `data/faq_docs.json` from the supplied repository ZIP. The input contained 20 records. The Department 3 audit register separately lists 21 source IDs and notes that `product_001` is absent from the JSON dataset.

## Results
- Standardized output records: 20
- Records with source metadata marked verified: 12
- Records marked unverified: 8
- Records with a source URL: 14
- Records with no source URL: 6
- Records with independent owner approval evidenced in supplied audit: 0
- Records eligible for production ingestion at this time: 0

## Cleanup decisions
- Standardized field names and record shape across all 20 JSON records.
- Normalized line endings and surrounding/trailing whitespace only; substantive wording was not rewritten.
- Retained all 20 records; no records were deleted or merged.
- Retained `faq-005` and the `product_001` inventory mismatch as an unresolved audit issue. `product_001` was not fabricated or recreated because its full source content is absent from the JSON.
- Kept product and general-finance modules distinct.
- Missing source URLs/dates remain JSON null where the record has no evidenced value.
- Existing `verified` flags are represented as `metadata_marked_verified`, not as independent approval.
- Existing audit documents are included as governance evidence, not marked as approved customer-facing content.

## Known limitations
- No assigned source owners or independently confirmed approvals were present in the supplied audit.
- Product workflows, privacy/security claims, and current report/export steps still require authorized confirmation where identified by the existing audit.
- The source ZIP contains a broad repository. This pass standardizes the FAQ/knowledge JSON and includes the audit governance documents; it does not convert every internal engineering note, test report, or planning file into customer-facing knowledge.

## Validation
The included validator checks JSON parsing, required metadata keys, non-empty content, unique IDs, supported status values, and the expected 20-record count. Run it from the package root using:
`python scripts/validate_department3_knowledge.py`
