# Knowledge Base Management

## Purpose
This document describes how to maintain the HisabDo financial assistant knowledge base.

## Knowledge Base Location
The primary FAQ knowledge-base file is `data/faq_docs.json`. Related implementation files include:
- `src/financial_assistant/faq_rag.py`
- `src/financial_assistant/rag/knowledge_base.py`
- `src/financial_assistant/rag/retriever.py`
- `src/financial_assistant/rag_pipeline.py`
- `src/financial_assistant/vector_store.py`

Confirm the current code paths before changing the knowledge-base format or retrieval process.

## Maintenance Procedure
1. Create a separate branch before editing knowledge-base content.
2. Review existing entries in `data/faq_docs.json` to avoid duplicates.
3. Add or update entries using the same JSON structure as existing records.
4. Use clear, concise answers that match verified product behaviour.
5. Do not add unsupported financial claims, unverified application instructions, credentials, or real customer information.
6. Check that the JSON is valid.
7. Run the automated tests and review retrieval answers for changed entries.
8. Review the changes before merging them into the target branch.

## JSON Validation
From the repository root, run:

```powershell
python -c "import json; json.load(open('data/faq_docs.json', encoding='utf-8')); print('FAQ JSON is valid')"
```

## Content Review Checklist
- [ ] Entries are accurate and relevant to HisabDo.
- [ ] No duplicate or contradictory answers were introduced.
- [ ] English and supported Urdu/Roman Urdu wording is understandable.
- [ ] Answers do not expose private financial information.
- [ ] JSON validation succeeds.
- [ ] Relevant automated tests pass.
- [ ] A reviewer approves the change.

## Backup and Recovery
Use Git to review and restore intentional knowledge-base changes. Do not overwrite the current file with a backup without comparing the contents first. Keep backups free of credentials and personal financial data.

## Ownership
The maintainer and reviewer should be assigned by the project team. Production updates require review and testing.
