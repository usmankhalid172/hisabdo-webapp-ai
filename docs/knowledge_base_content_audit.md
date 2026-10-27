# Knowledge Base Content Audit

## Scope
Reviewed `data/faq_docs.json` and `data/sample_financial_knowledge.json` for content organization, duplicate records, metadata, and JSON validity.

## Current Inventory
- `data/faq_docs.json`: 12 FAQ documents; used by the active FAQ chatbot retriever.
- `data/sample_financial_knowledge.json`: 6 financial knowledge documents; used by the financial retrieval tests.
- Both files parse as valid JSON.
- Required metadata fields checked: `title`, `section`, `category`, `source_url`, `language`, `updated_date`, and `product_area`.

## Duplicate Findings
Six exact duplicate records exist across the two files:
- `finance_001` ? What is profit?
- `finance_002` ? What is revenue?
- `finance_003` ? What is an expense?
- `finance_004` ? What is cash flow?
- `finance_005` ? Why should customer balances be tracked?
- `finance_006` ? Why should business expenses be categorized?

These records were not deleted because the FAQ file serves the chatbot and the sample knowledge file is used by retrieval tests. Removing either copy without an approved canonical-source migration could break an existing workflow.

## Content Cleanup Review
The reviewed FAQ text contains question-and-answer content; no obvious navigation menus or footer text were found in the supplied records. No content was rewritten during this metadata task, to avoid changing the original meaning without source verification.

## Metadata and Source Verification
- `product_area` metadata was added to both files.
- Retrieval tests: `tests/test_retrieval.py` ? 2 passed, 1 warning.
- Source URLs and last-updated dates are currently null in the FAQ records. They remain unfilled because approved source URLs and verification dates were not available during this review.
- Product-specific statements, including export options and privacy claims, still require confirmation against approved product documentation before being marked verified.
- No claims are made that the sources are approved, current, or fully verified.

## Recommended Follow-up
1. Obtain approved source URLs and content owners for each knowledge item.
2. Verify product-specific statements against current approved documentation.
3. Record the verification date and review/expiry policy.
4. Decide whether shared definitions should be maintained in one canonical source, then update dependent tests and retriever configuration before removing duplicates.
5. Re-run JSON, metadata, and retrieval tests after any approved content changes.

## Structured Chunk Export

- Output file: `data/structured_knowledge_chunks.json`
- Total chunks exported: 18
- Chunk IDs: 18 unique IDs; no duplicates found
- Chunk structure includes document ID, title, section, category, text, source URL, language, update date, product area, and source file.
- Validation result: PASS for metadata and non-empty text.
- Each current FAQ/Q&A is stored as one chunk because the entries are short.
- Duplicate content across the two input files remains documented for future canonical-source cleanup.
- Source URLs and update dates remain null where they have not been verified; they were not invented.


## Structured Chunk Export

- Output file: `data/structured_knowledge_chunks.json`
- Total chunks exported: 18
- Chunk IDs: 18 unique IDs; no duplicates found
- Chunk structure includes document ID, title, section, category, text, source URL, language, update date, product area, and source file.
- Validation result: PASS for metadata and non-empty text.
- Each current FAQ/Q&A is stored as one chunk because the entries are short.
- Duplicate content across the two input files remains documented for future canonical-source cleanup.
- Source URLs and update dates remain null where they have not been verified; they were not invented.

