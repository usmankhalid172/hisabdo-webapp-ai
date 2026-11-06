# Department 4 — Consolidated Source Register & Missing/Outdated Content Summary

**Prepared by:** Muhammad Daniyal  
**Task:** Submission Coordination & Knowledge Source Master Register Review  
**Review date:** 6 November 2026  
**Inputs:** All audit logs and registers supplied in `oversight and knowledge base audit.zip`

## Executive decision

**Recommendation: CONDITIONAL HOLD for unconditional department-wide approval.** The supplied files support a useful provisional register, but they do not support repeating the clearance report’s blanket “100% authorized / zero blockers” conclusion. The system-wide audit explicitly says approval evidence was not attached and identifies unresolved cross-domain issues. Mark affected entries `pending_review` until evidence and owner decisions are recorded.

## Reconciled inventory

| Measure | Supplied evidence | Consolidated interpretation |
|---|---:|---|
| Main chatbot index | 115 URLs / 976 chunks | 77 XICTEK URLs / 571 chunks + 38 HisabDo URLs / 405 chunks per system audit |
| HisabDo repository audit | 421 `hisabdo.app` chunks | **Mismatch:** 421 vs 405; reconcile branch/snapshot/crawl version |
| Register coverage | 62 of 115 pages | 53 indexed pages have no matching register in the received package |
| Blog | 47 articles | 0 exact duplicate bodies; 154 near-duplicate article pairs (>85%); 1 near-duplicate title group |
| Index deduplication | 0 exact duplicate chunks | 44 near-duplicate chunk pairs (80%+); not directly comparable to article-body count |
| Live page check | 14 pages opened | All loaded real content in the audit; exact HTTP codes and redirect chains were not captured |

## Critical cross-domain findings

1. **Canonical URL host mismatch (P0):** index uses `https://xicteksystems.com` for all 77 corporate URLs; the website declares `https://www.xicteksystems.com`. Both host forms reportedly serve the same content without redirect. The blog audit’s www-only approval rule therefore rejects all 47 non-www blog URLs stored in the index. Choose one canonical host, implement/verify redirects, and normalize registers and index.
2. **Approval evidence gap (P0):** team clearance says 100% signed off, but the system audit says signed approval evidence is absent from the supplied files. Keep affected sources pending until sign-off records are attached.
3. **Careers status unconfirmed (P1):** four roles (Senior Full-Stack Developer, Mobile App Developer, Cloud Solutions Architect, UI/UX Designer), internship cohort details, and the 3–5 business-day application-review promise are pending HR/hiring-owner verification. Missing posting dates are not proof a vacancy is closed.
4. **Contact form contradiction (P1):** contact log says form field schema is not published in static docs; system audit reports a 4 Nov live check found Full Name, Email and Message required. Recheck and update the source record.
5. **HisabDo product wording conflicts (P1):** offline use, sync scope, backup/restore, encryption/security, Android minimum version and precision metrics need normalization or owner evidence. Use FAQ/Privacy Policy qualifiers over broad marketing copy.
6. **Portfolio case-study authorization (P1):** three anonymous logistics, healthcare and FinTech case narratives contain quantified outcomes but lack client identity, dated evidence and written publication approval. Hold them from chatbot reuse. HisabDo product showcase is approved only within the narrow publicly displayed product identity/features scope.
7. **About/core services inconsistencies (P1):** 13 homepage claims lack evidence; cloud scope differs (AWS-only home card vs AWS+Azure elsewhere); overlapping cloud/DevOps services and standalone ERP/API/UI/UX/desktop offerings need owner confirmation.
8. **Duplicate content (P1/P2):** blog’s 154 near-duplicate pairs are full article comparisons; system’s 44 pairs are index chunk comparisons. Keep the counts separate. Six service topics overlap pillar pages; repeated template paragraphs and listing pages should be consolidated/excluded.
9. **Missing source records (P1):** 53 indexed pages were not represented in received registers. The audit groups many under pillars, service subpages, people profiles, listing pages and other domains; the exact 53-URL list must be obtained before final approval.
10. **Metadata gap (P1):** index chunks currently store only id/title/url/text. Add entity, category, content owner, approval status, crawl date, content hash, effective date, duplicate mapping and review due date.

## Domain-level disposition

| Domain | Disposition | Key action |
|---|---|---|
| Contact & Locations | Pending reconciliation | Recheck required form fields; attach sign-off; retain strict fallback for unpublished address, phone, office hours and SLA details. |
| About & Core Services | Pending owner decisions | Hold unsupported metrics; align service names/scope; obtain missing company facts and sign-off. |
| Careers & Internship | Pending HR | Confirm roles, dates, requirements, application route, internship cohort and response-time promise. |
| Portfolio | Interim / limited | Keep HisabDo showcase within approved public scope; hold anonymous client case studies and metrics. |
| Blog & News | Pending technical/content cleanup | Fix canonical-host rule; review near duplicates and template repetition; attach approval evidence. |
| HisabDo product references | Separate namespace; pending claim cleanup | Preserve product boundary; refresh stale chunks and qualify product claims.
| System-wide index | Pending | Reconcile 53 unregistered pages, 421/405 chunk mismatch, URL host and missing metadata. |

## Missing / outdated content and ownership log

| Priority | Issue | Owner / responsible group | Required resolution |
|---|---|---|---|
| P0 | Canonical host inconsistency | Team lead + website team + ingestion owner | Set one canonical host, add 301 redirect, normalize all registers and index URLs, repair blog validation rule. |
| P0 | Approval evidence absent | All domain owners + team lead | Attach signed notes/emails per domain and downgrade unsupported records to pending_review until evidence exists. |
| P1 | Careers vacancies and internship pending | Farah Naz / HR + hiring owners | Confirm active vacancies, dates, requirements, application route, cohort status, capacity and turnaround promise. |
| P1 | Contact form required fields conflict | Kamran Aslam + Business Operations | Recheck live form; record evidence and update static source/guardrail. |
| P1 | HisabDo offline and sync wording | Eiman Ayesha / product owner | Normalize wording; separate local offline features, account functions, sync, backup and restore. |
| P1 | HisabDo security claims unsupported | HisabDo product + security/legal | Hold precise claims pending documented security evidence; use policy wording. |
| P1 | HisabDo Android compatibility stale chunk | HisabDo product / ingestion owner | Refresh chunk and verify current Play listing. |
| P1 | HisabDo sync and backup scope | HisabDo product owner | Rewrite KB as separate concepts and get product owner confirmation of restore paths. |
| P1 | Portfolio client case studies unapproved | Portfolio owner + legal/client approver | Exclude/hold case studies and outcome claims until evidence + written authorization; retain HisabDo product showcase only within scope. |
| P1 | Homepage and core services unsupported claims | Shahid Imran + brand owner | Hold metrics; align canonical service names and get engineering/brand owner sign-off. |
| P1 | Near-duplicate content | Blog/content team + ingestion owner | Do not conflate counts; identify canonical fact chunks, mark duplicate_of, rewrite repeated template paragraphs. |
| P1 | Missing 53 source records | Team lead + domain owners | Obtain full URL list, assign owners, exclude people/listing pages where not relevant, record exclusions. |
| P1 | HisabDo corpus count mismatch | HisabDo auditor + ingestion owner | Reconcile snapshot/branch/crawl version; record source commit and extraction timestamp. |
| P2 | HisabDo currencies and languages differ | HisabDo product owner | Do not merge lists; use only explicitly enumerated current FAQ values pending owner confirmation. |
| P2 | Terms freshness | HisabDo legal owner | Legal owner to confirm current Terms and effective date. |
| P2 | Listing pages and cross-domain duplicate facts | Ingestion + domain owners | Exclude listing pages, apply entity filters, choose one canonical page per service and tag duplicates. |
| P2 | Missing metadata on chunks | Ingestion owner | Add required metadata fields at next rebuild and enforce approved-only ingestion. |

## Source register contents

The accompanying workbook contains: (1) executive reconciliation, (2) consolidated source register for all individually identifiable sources in the supplied files, (3) issue/ownership log, (4) original Contact attribute register, (5) Careers source and purge logs, (6) 47-row Blog register, and (7) HisabDo claim findings. A tracking placeholder is included for the 53 unregistered pages; it is **not** a substitute for the missing URL-level list.

## Approval rules for final handover

- A source is `approved` only when its canonical URL, owner, approval evidence, last-verified date, crawl date and scope are recorded.
- Use `pending_review` for missing evidence, unresolved conflicts, stale chunks or failed/unrecorded link checks. Use `excluded` for out-of-scope pages with a reason.
- Keep XICTEK and HisabDo entity namespaces separate.
- Do not ingest unsupported performance/security metrics, unapproved client outcomes, expired/uncertain vacancies, or unverified contact attributes.
- Re-run URL/redirect and duplicate checks after canonicalization and before rebuild.

**Important limitation:** This is a consolidation of the supplied audit evidence, not an independent full crawl of all 115 URLs. The system audit itself reports that exact HTTP status codes/redirect chains were not captured.
