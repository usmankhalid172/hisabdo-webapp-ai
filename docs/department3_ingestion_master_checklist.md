# Department 3 Ingestion Master Checklist

## 1. Source readiness
- [ ] Confirm source ownership and authorization.
- [ ] Confirm content accuracy before ingestion.
- [ ] Keep unverified source URLs and dates null.
- [ ] Confirm JSON files are valid UTF 8.
- [ ] Confirm each source contains a list of records.

## 2. Supported knowledge sources
| Source | Expected records | Handling |
|---|---:|---|
| data/faq_docs.json | 12 | One complete FAQ per chunk |
| data/sample_financial_knowledge.json | 6 | Question, answer and keywords together |

## 3. Metadata validation
- [ ] Unique IDs within each source.
- [ ] Nonempty title, section, category, language and product area.
- [ ] Valid HTTP or HTTPS source URL, or null.
- [ ] Valid ISO date, or null.
- [ ] At least one valid knowledge content field.
- [ ] Preserve source identity when IDs overlap across files.

## 4. Chunking checks
- [ ] Keep short FAQs intact.
- [ ] Keep financial question, answer and keywords together.
- [ ] Keep table headers with their related rows.
- [ ] Split long workflows at paragraph boundaries.
- [ ] Split long documentation at heading and paragraph boundaries.
- [ ] Apply overlap only to long text that needs splitting.
- [ ] Check that chunks do not lose source metadata.

## 5. Automated ingestion
- [ ] Run scripts/department3_ingestion.py.
- [ ] Validate JSON parsing.
- [ ] Detect new records.
- [ ] Detect modified records using SHA 256 content hashes.
- [ ] Detect deleted records against the previous manifest.
- [ ] Detect duplicate IDs within each source.
- [ ] Detect repeated content within each source.
- [ ] Record failed source files and malformed records.
- [ ] Review the generated execution report.
- [ ] Verify generated chunk IDs are unique.

## 6. Retrieval and release checks
- [ ] Run the full pytest suite.
- [ ] Run retrieval evaluation after knowledge changes.
- [ ] Confirm personal account values are not stored in shared knowledge.
- [ ] Review retrieval quality and relevance threshold.
- [ ] Obtain content owner approval before production publication.
- [ ] Keep a copy of the previous approved knowledge assets.

## 7. Current execution evidence
- Sources processed: 2.
- Records processed: 18.
- Chunks generated: 18.
- Duplicate IDs: 0.
- Duplicate content: 0.
- Failed sources: 0.
- Parsing and record errors: 0.
- Full tests: 325 passed, 4 skipped, 1 warning.
- Current ingestion scope: local JSON sources only.

## 8. Open items
- [ ] Verify and approve source URLs and update dates.
- [ ] Add approved long form documentation and workflow sources.
- [ ] Add actual feature table ingestion when a verified table source exists.
- [ ] Add remote page fetching only after an approved source and fetch policy exist.
- [ ] Select and test a neural embedding model if semantic embeddings are required.
- [ ] Select and test a persistent vector database if persistent indexing is required.
- [ ] Add production ingestion approval and rollback controls.

Current status: Local JSON ingestion implemented and tested. Production source approval and external vector infrastructure are not configured.
