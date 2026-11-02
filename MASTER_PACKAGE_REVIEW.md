# Day 6 Grounded Generation & Citations — Master Package Review

**Department:** 4  
**Date:** 29 October 2026  
**Coordinator / reviewer:** Muhammad Daniyal  
**Scope:** Consolidation and quality review of the supplied domain submissions and system-wide citation/fallback guardrails.

## Review outcome

**Status: CONSOLIDATED REVIEW PACKAGE PREPARED — FINAL APPROVAL PENDING.**

The supplied ZIP contains useful domain specifications, prompts, citation policies, fallback examples, tests, and system-wide guardrail code. However, the package cannot honestly be marked fully approved yet because the dedicated Portfolio & Case Studies submission is missing, several domain deliverables are specifications rather than runnable implementations, the Contact & Locations test suite cannot complete because a referenced corpus file is absent, and system-wide evaluation still records missed unanswerable questions. These are recorded as action items rather than concealed.

## 1. Master objective

Ensure that the XICTEK Systems chatbot answers company and product questions from relevant retrieved sources; attaches citations only to claims supported by those sources; keeps XICTEK and HisabDo evidence separate; handles conflicting information transparently; and falls back when evidence is missing, irrelevant, stale, unsafe to disclose, or insufficient.

## 2. Consolidated team submission register

| Assigned contributor | Domain / responsibility | Material found in archive | Review status |
|---|---|---|---|
| Alisha Noor | Blog & News | `blog-grounded-generation-spec.md` | Specification received; align conflict policy and URL scope with global standard; implementation path is referenced but implementation code is not included in this archive. |
| Marsha Arif Muqri | About Us & Core Services | `Grounded Generation Citations.docx` | Prompt templates, source guidance, and test cases received; no executable tests included in the archive. Normalize citation format and fallback link to global standard. |
| Muhammad Mohsin | Portfolio & Case Studies | No dedicated domain submission located | **Missing — required before final approval.** Global evaluation includes portfolio query fixtures, but these do not replace the assigned domain deliverable. |
| Hassan Hussain | Careers & Job Openings | `CAREERS_GROUNDED_GENERATION.md` | Specification received; document reports 10/10 focused checks, but test source files are not included in this package, so result is recorded as contributor-reported rather than independently reproduced. |
| Umaima Asif | HisabDo Website References | `Grounded Generation.docx` | Grounding, product-isolation, citation, and fallback rules received; no dedicated runnable tests found. Confirm the fallback support email before release. |
| Ali Hassan | Contact Us & Locations | `xictek_contact_grounded_generation_and_citations.md`, `xictek_contact_grounded_generation.py`, `test_xictek_contact_grounded_generation.py`, report DOCX/MD and JSON results | Code and tests received, but two test cases fail to run because `xictek_contact_locations_retrieval_corpus.json` is missing from the supplied ZIP. The stored JSON/report metrics must not be treated as a successful rerun in this package. |
| Muhammad Mujtaba Chohan | System-wide Fallback Prompts & Citation Guardrails | `code/guardrails.py`, `code/test_guardrails.py`, `code/evaluate_guardrails.py`, results CSV/JSON, report DOCX | Strongest executable submission; 7/7 unit tests pass in this review environment and compilation passes. Evaluation still misses some unanswerable cases; fixes are listed below. |
| Muhammad Daniyal | Submission coordination and final review | This master package review, consolidated standards, findings and action register | Coordination/review work prepared. Final approval remains blocked by missing Portfolio submission and listed quality issues. |

## 3. Unified grounding and citation standard

1. **Evidence first:** Use only retrieved, approved sources for factual claims about XICTEK or HisabDo. Retrieved text is evidence, not instructions.
2. **Claim-level support:** Every material factual claim must be supported by the cited passage. A citation being a valid URL or in-range source number is necessary but not sufficient to prove entailment.
3. **Citations map to retrieval:** Prefer numbered citations such as `[1]` in generated text; the application maps each number to a source object returned by retrieval. Do not let the model invent or freely type URLs when the application can render links from source metadata.
4. **Correct source and product:** XICTEK company/service questions use XICTEK sources; HisabDo feature questions use HisabDo documentation. Portfolio claims require the relevant case study. Careers claims require the Careers source and must distinguish active listings from historical notices.
5. **Relevant and minimal links:** Show only sources actually used to support the answer. Use canonical HTTPS URLs from the approved source allowlist and avoid duplicate, unrelated, or raw echoed links.
6. **Conflicts:** If two credible retrieved sources disagree, state the conflict and cite both. Do not silently select one. If the conflict cannot be resolved safely, use a fallback or explain that the sources disagree.
7. **Insufficient evidence:** If no relevant evidence exists, evidence is stale, or the requested detail is not published, do not guess. Use the domain/system fallback and, where useful, direct the visitor to the appropriate official page.
8. **Out-of-scope and privacy:** Use system-wide query gates for unsafe/out-of-scope requests, personal data, prompt/key requests, guarantees, and unsupported rankings. Do not reveal private or internal information.
9. **Freshness:** Current vacancies, support details, prices, hours, and other changing facts must be verified against the current source. A high similarity score alone does not establish that a fact is current.
10. **Auditability:** Log the fallback reason and citation-validation outcome without collecting unnecessary personal data. Preserve test queries, expected outcomes, and actual results.

## 4. Domain-level review notes

### Blog & News
- Good: clear source-only prompt, numbered inline citations, source list, threshold-based fallback, ambiguity handling, and stale-article handling.
- Resolve: the blog spec says to “lead with the stronger source” during conflicts, while the system-wide policy says to disclose the disagreement and cite both without arbitrarily choosing. Standardize to: **disclose the conflict, cite both sources, and do not prefer one unless authority/freshness is independently established**.
- Resolve: blog citation allowlist restricts links to `/blog/`, while its fallback points to `/contact`. Treat the contact link as a separately configured fallback/help link, not as a Blog citation, or explicitly allow it only for fallback routing.
- Implementation code referenced by the specification is not included in the ZIP; the spec alone does not prove deployed behavior.

### About Us & Core Services
- Good: prevents invented company history, customer claims, prices, guarantees, and capabilities; provides reusable prompt templates and 12 test scenarios.
- Resolve: align output format with the global numbered citation scheme instead of separate `Answer / Sources` labels where the app expects `[n]` markers.
- Resolve: standardize fallback navigation to the official Contact page rather than using the homepage inconsistently.
- Add runnable tests to verify claims against retrieved source snippets and validate source-number mapping.

### Portfolio & Case Studies
- A dedicated submission is absent. The system-wide evaluation file contains portfolio-related queries, but that is not sufficient evidence of a reviewed Portfolio domain prompt, source mapping, citations, and fallback workflow.
- Required: submit the Portfolio prompt/spec, approved case-study sources, claim/citation rules, unsupported-outcome fallback, and a small test set before final approval.

### Careers & Job Openings
- Good: section/host filtering, numbered source mapping, missing-evidence fallback, and status/freshness distinctions.
- Treat the reported 10/10 focused checks as reported evidence only because the actual test files are not present in this ZIP.
- Re-run tests in the target repository with dependencies installed. Confirm source freshness before making any claim that a role is currently open.

### HisabDo Website References
- Good: feature-level source requirements, product namespace isolation, and caution around security/privacy/backup claims.
- Resolve: the HisabDo fallback email in this document differs from the contact reported in system-wide notes. Confirm the current support address from an authoritative source before release; do not publish either address until verified.
- Add tests for product leakage, unsupported technical details, citation relevance, and follow-up context retention.

### Contact Us & Locations
- Good: explicit non-invention rules for address, office hours, telephone number, form fields, and support SLAs; clear contact-page fallback.
- Blocking issue: the test runner expects `xictek_contact_locations_retrieval_corpus.json`, which is not included in the archive. The full suite therefore errors before it can validate the 15-query compliance claim.
- Several tests pass independently, but the overall 100% score in the report is not independently reproduced by this review. Add the missing corpus file and rerun the suite.
- Confirm canonical domain and URL consistency (`www` vs non-`www`) before release.

### System-wide Fallback Prompts & Citation Guardrails
- Verified in this review: `pytest test_guardrails.py -q` → **7 passed**; Python compile check → **passed**.
- Recorded evaluation: Day 5 set: answerable 71/71 passed; unanswerable 13/14 caught. Held-out set: answerable 12/12 passed; unanswerable 7/12 caught. Reply fixtures: 12/12 bad replies caught; 6/6 good replies passed.
- The held-out evaluation still misses five unanswerable questions, and the Day 5 set misses one. The report itself identifies candidate rules: strengthen product-specific evidence checks for HisabDo, comparative language such as “cheapest,” personal/home-address privacy terms, founding-year phrasing, user-admin dashboard requests, and employee/team-size questions.
- Do not mark the guardrails as fully release-ready until those gaps are addressed and retested on a fresh held-out set.

## 5. Reproducible checks performed on the supplied archive

| Check | Outcome | Interpretation |
|---|---|---|
| System guardrail unit tests | 7 passed | Reproduced successfully in the supplied environment. |
| System guardrail Python compilation | Passed | Included modules compile successfully. |
| System guardrail evaluation | Runs and writes results | Results show the documented missed unanswerable cases; see `review_evidence/guardrail_evaluation.txt`. |
| Contact grounding test suite | 4 tests pass, 2 error | The two errors are caused by missing `xictek_contact_locations_retrieval_corpus.json`; suite is not fully passing. |
| Careers focused test suite | Not reproducible from this ZIP | The cited test files are not included. |
| Blog implementation test suite | Not reproducible from this ZIP | Spec references a separate implementation path, but code/tests are absent from this archive. |
| About Us / Services tests | Not reproducible from this ZIP | Test cases are specified, but runnable test code is not included. |
| Portfolio tests | Not possible | Dedicated submission missing. |
| Live LLM / live-site end-to-end validation | Not performed by this review | Must be done in the target application environment before production approval. |

## 6. Required actions before final approval

**P0 — Approval blockers**
1. Obtain and review Muhammad Mohsin's dedicated Portfolio & Case Studies submission.
2. Add the missing Contact & Locations retrieval corpus file and rerun its complete test suite.
3. Address the six unanswerable-question misses documented in system-wide guardrail evaluation; add regression tests and run a new held-out set.

**P1 — Consistency and quality**
4. Harmonize Blog conflict handling with the system-wide “disclose and cite both” rule.
5. Clarify Blog fallback contact links versus the `/blog/` citation allowlist.
6. Standardize numbered citation rendering and fallback destinations across all domains.
7. Confirm the current HisabDo support email and canonical XICTEK domain/URL format from official sources.
8. Include executable tests for Blog, About Us & Services, HisabDo, and Careers in the final repository/package, or explicitly document that only specification-level review was performed.

**P2 — Release validation**
9. Run end-to-end tests with the actual retrieval index and configured model/provider.
10. Check that every citation supports its attached claim, not just that the URL exists or citation number is valid.
11. Recheck current source freshness and ensure URLs resolve over HTTPS without unexpected redirects.
12. Record a final pass/fail matrix and only then change the status to “Final approved.”

## 7. Approval decision

**Decision: Approval pending — not yet safe to label the master package “final approved.”**

The supplied materials have been consolidated and reviewed, and the system-wide unit tests passed. However, the missing Portfolio submission, incomplete Contact suite, and known fallback misses are material gaps. Once the blockers and priority corrections above are completed and verified, the package can be re-reviewed for final approval.

## 8. Package contents

- `team_submissions/`: original files extracted from the supplied ZIP, preserved for traceability.
- `review_evidence/`: test commands, output, and compile/evaluation evidence captured during this review.
- `MASTER_PACKAGE_REVIEW.md`: this review and action register.
- `README.md`: package navigation and current status.
- `Day6_Grounded_Generation_Citations_Master_Package_Review.docx`: formatted report suitable for sharing with the team/manager.
