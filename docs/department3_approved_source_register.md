# Department 3 Approved Source Register

Audit date: 2026-11-06
Overall status: PARTIAL, formal approval pending

## Source Register

| Source asset | Category | Owner | URL or location | Last verified | Scheduled review | Status |
|---|---|---|---|---|---|---|
| faq_docs.json | Product FAQs | Unassigned, Product Owner required | data/faq_docs.json | 2026-11-06, repository inspection only | 2026-12-06, proposed | Approval pending |
| sample_financial_knowledge.json | Financial reference content | Unassigned, Finance Content Owner required | data/sample_financial_knowledge.json | 2026-11-06, repository inspection only | 2026-12-06, proposed | Approval pending |
| knowledge_base_management.md | Knowledge maintenance procedure | Unassigned, Knowledge Base Owner required | docs/knowledge_base_management.md | 2026-11-06, repository inspection only | 2026-12-06, proposed | Internal procedure, approval pending |
| product-guidance-pdf-verification.md | Product workflow guide | Unassigned, Product Owner required | docs/product-guidance-pdf-verification.md | 2026-11-06, repository inspection only | 2026-12-06, proposed | Live verification pending |

## Inventory Findings

- FAQ file contains 12 records.
- Financial knowledge file contains 6 records.
- All 18 records have missing source_url and updated_date values.
- No authoritative public product documentation URL was confirmed.
- Named content owners and formal approval records were not found.
- Repository inspection does not establish product accuracy or formal approval.

## Duplicate Content Review

Six matching financial definitions appear in both files:
finance_001, finance_002, finance_003, finance_004, finance_005, finance_006.

These records have not been deleted because both files support existing workflows. A canonical source decision and dependency migration are required before removal.

FAQ faq-003 requires privacy owner approval.
FAQ faq-002 requires confirmation of current automatic categorization behavior.
FAQ faq-004 and finance_004 require review for overlapping cash flow explanations.

## Review Schedule

2026-12-06 is a proposed review date only. The Product Owner must approve the review interval and assign named owners.

## Approval Rule

No source may be marked approved until its owner, authoritative URL, accuracy, approval evidence, and review schedule are confirmed.
