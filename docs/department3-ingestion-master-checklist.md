# Department 3 Ingestion Master Checklist

## Source preparation
- [x] Identify active FAQ source and staging source.
- [x] Confirm 16 staging records.
- [x] Confirm IDs, titles, sections, categories and modules.
- [ ] Obtain source-owner approval.
- [ ] Verify official source URLs and last-updated dates.
- [ ] Review pending source-verification metadata.

## Chunking and embeddings
- [x] Document FAQ chunking strategy.
- [x] Document table chunking strategy.
- [x] Document workflow chunking strategy.
- [x] Document long-document chunking strategy.
- [x] Record current embedding implementation and limitations.
- [ ] Benchmark chunking against representative tables and workflows.
- [ ] Pin and verify the production embedding environment.

## Automated ingestion
- [x] Create repeatable staging ingestion script.
- [x] Generate deterministic content hashes.
- [x] Track added, modified, deleted and unchanged records.
- [x] Detect duplicate IDs and duplicate content.
- [x] Capture malformed records and vector parsing errors.
- [x] Report unresolved source URLs.
- [ ] Implement and test live page fetching when approved URLs exist.
- [ ] Integrate approved embedding generation and vector-index persistence.

## Validation and release
- [ ] Run automated ingestion tests.
- [ ] Run full project test suite.
- [ ] Review execution report and generated chunks.
- [ ] Confirm active FAQ source remains unchanged.
- [ ] Obtain approval before promoting staging data.
- [ ] Commit reviewed changes.
- [ ] Push only after explicit approval.
