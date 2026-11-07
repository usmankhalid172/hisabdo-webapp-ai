# Department 3 – Approved Source Register

## 1. Audit Summary

| Metric | Finding |
|---|---:|
| Source records in existing audit CSV | 21 |
| Records marked verified in metadata | 13 |
| Records marked unverified | 8 |
| Assigned source owners | 0 |
| Independently confirmed product-owner approvals | 0 |
| Records with documented scheduled review dates | 0 |
| FAQ JSON records | 20 |
| CSV records missing from FAQ JSON | 1 (`product_001`) |

**Approval note:** No source is classified as independently approved in this audit. The `Verified=True` field represents existing metadata, not independent evidence of product-owner approval.

## 2. Source Register

The dates below are copied from the existing audit metadata. They are not represented as newly completed independent verification dates.

| ID | Category | Source URL / Path | Designated Owner | Last-Verified Date | Last-Reviewed Date in Metadata | Scheduled Review Date | Approval Status |
|---|---|---|---|---|---|---|---|
| faq-001 | product_faq | https://hisabdo.app/faq | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| faq-002 | product_faq | Not provided | Pending assignment | Not independently verified | Not recorded | Not scheduled | Unverified |
| faq-003 | product_faq | Not provided | Pending assignment | Not independently verified | Not recorded | Not scheduled | Privacy confirmation required |
| faq-004 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| faq-005 | product_faq | https://hisabdo.app/faq | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| faq-006 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| finance_001 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| finance_002 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| finance_003 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| finance_004 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| finance_005 | finance_faq | Not provided | Pending assignment | Not independently verified | Not recorded | Not scheduled | Unverified |
| finance_006 | finance_faq | Not provided in audit CSV | Pending assignment | Not independently verified | Not recorded | Not scheduled | Unverified; source confirmation required |
| finance_007 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| finance_008 | finance_faq | [OpenStax Section 2.1](https://openstax.org/books/principles-of-financial-accounting/pages/2-1-describe-the-income-statement-statement-of-owners-equity-balance-sheet-and-statement-of-cash-flows-and-how-they-interrelate) | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending |
| finance_009 | finance_faq | Not provided | Pending assignment | Not independently verified | Not recorded | Not scheduled | Unverified |
| finance_010 | finance_faq | Not provided in audit CSV | Pending assignment | Not independently verified | Not recorded | Not scheduled | Unverified; source confirmation required |
| product_001 | product_documentation | https://hisabdo.app/faq | Pending assignment | Not independently verified | 2026-10-13 | Not scheduled | Approval pending; missing from FAQ JSON |
| product_002 | product_documentation | Not provided | Pending assignment | Not independently verified | Not recorded | Not scheduled | Engineering confirmation required |
| product_003 | product_documentation | Not provided | Pending assignment | Not independently verified | Not recorded | Not scheduled | Engineering review required |
| faq-khata-guidance | product_faq | https://hisabdo.app/faq | Pending assignment | Not independently verified | 2026-10-16 | Not scheduled | Approval pending |
| faq-udhar-guidance | product_faq | Not provided | Pending assignment | Not independently verified | 2026-10-16 | Not scheduled | Approval and source accuracy pending |

## 3. Supporting Workflow and Technical Documentation Reviewed

These repository documents were inspected as internal evidence. They are not automatically classified as approved customer-facing guides.

| Document | Category | Repository Path | Owner | Last-Verified Date | Scheduled Review | Status |
|---|---|---|---|---|---|---|---|
| Knowledge Base Maintenance | Maintenance procedure | `docs/knowledge_base_maintenance.md` | Not specified | Not recorded | Not scheduled | Internal procedure; reviewer assignment pending |
| Source Actions | Governance and privacy actions | `docs/knowledge_source_actions.md` | Not specified | Not recorded | Not scheduled | Internal audit evidence |
| Grounded Response and Citation Guidelines | Chatbot response workflow | `docs/chatbot-grounded-response-and-citation-guidelines.md` | Not specified | Not recorded | Not scheduled | Intended behavior; runtime validation required |
| Smart Expense Categorization Plan | Feature planning | `docs/smart_expense_categorization_plan.md` | Not specified | Not recorded | Not scheduled | Internal planning document |
| Day 20 Smart Expense Finalization | Feature implementation | `docs/day20-smart-expense-finalization.md` | Not specified | Not recorded | Not scheduled | Internal implementation evidence |
| Day 21–22 Integration Readiness | Integration workflow | `docs/day21-22-expense-integration-readiness.md` | Not specified | Not recorded | Not scheduled | Internal testing evidence; production readiness not established |
| Day 25 User Flow Bug Test Report | Workflow testing | `docs/day25_user_flow_bug_test_report.md` | Not specified | Not recorded | Not scheduled | Internal test evidence; integration blockers recorded |
| Day 17 AI Use Case Improvement Review | AI workflow review | `docs/day17-ai-use-case-improvement-review.md` | Not specified | Not recorded | Not scheduled | Internal improvement review, not customer feedback |

## 4. Source Governance Findings

1. All 21 source records lack a designated owner.
2. No source has an approved scheduled review date or documented expiry policy.
3. Eight records are marked unverified.
4. Thirteen records are marked verified in metadata, but independent approval evidence is missing.
5. Nine CSV records use `Not provided` for their source URL.
6. The CSV contains 21 source IDs, while the FAQ JSON contains 20 records. `product_001` is missing from the JSON inventory.
7. Internal technical and planning documents do not independently establish current customer-facing workflows.

## 5. Duplicate and Contradictory Content Review

The following candidate pairs and groups were compared using the available FAQ JSON and audit CSV records:

- `faq-005` and `product_001`: Both concern report download/export guidance and share the same recorded source and review date. However, `product_001` is absent from `faq_docs.json`, so its original content is unavailable. Exact duplication cannot be established. Retain both inventory records pending reconciliation and owner confirmation.
- `faq-001` and `faq-khata-guidance`: Related product context, but one is a general product introduction and the other focuses on Khata and ledger usage. Retain both.
- `faq-004` and `finance_004`: One explains a cash flow statement and its activity groups; the other defines cash flow. Retain both.
- `faq-006`, `finance_001`, `finance_007`, and `finance_008`: These address different explanations and comparisons involving profit, revenue, and cash flow. Retain all four.

No exact duplicate or confirmed contradictory pair was established among the inspected candidates. No entries were deleted or merged. Any future consolidation requires original content comparison and authorized owner approval.

## 6. Review Schedule Recommendation

Proposed schedule, pending project-owner approval:

- Review product guidance whenever a relevant product feature or workflow changes.
- Review the complete source inventory at least quarterly.
- Record the reviewer, verification date, approval evidence, and next review date for each source.
- Revalidate source links and remove superseded material only after comparison and approval.

No future review dates have been invented or entered as approved dates.

## 7. Required Actions

1. Assign a designated owner to each source.
2. Obtain written product-owner or authorized reviewer approval.
3. Verify the accuracy and current availability of product-specific claims.
4. Supply missing source URLs or documented internal source paths.
5. Resolve the `product_001` inventory mismatch.
6. Duplicate candidate comparisons are documented; resolve the missing `product_001` content and obtain owner approval before any consolidation.
7. Confirm an authorized feedback source or approve an alternative.
8. Approve a periodic review schedule and record actual next review dates.

## 8. Audit Scope and Limitations

This register reflects the repository records and selected documentation inspected during the Department 3 audit. It does not establish that all external product sources, customer reviews, or feedback systems have been inspected.

No owner, approval date, independent verification date, or scheduled review date is claimed where supporting evidence was unavailable.
