# Department 3 Final Defect Closure Report

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-17 · **Branch:** `FahadZubairi_AI`
**Log:** [dept3-final-defect-triage-log.md](dept3-final-defect-triage-log.md) (`data/dept3_e2e/defect_triage.csv`, 43 entries)
**Companions:** [Production Configuration Freeze Spec](dept3-production-config-freeze-spec.md) ·
[Operations Runbook](dept3-operations-runbook.md) · [End-to-end regression report](dept3-e2e-regression-report.md)

## 1. Result

The Day 8 log had **34 open or partial items** (P0 5, P1 14, P2 11, P3 4). After this pass: **18 open or partial**
(P0 1, P1 9, P2 5, P3 3), **3 accepted** with a stated reason, **22 fixed** (13 from the original 32, 9 found by the
end-to-end runs). Nothing that passed before fails now.

| Priority | Open on 16 Nov | Open now | Closed or accepted |
|---|---|---|---|
| P0 | 5 | **1** (D3-01, mock backend) | 4 |
| P1 (high) | 14 | 9 | 5 |
| **P2 (medium)** | 11 | **5** | 6 |
| **P3 (low)** | 4 | **3** | 1 |

Every open P2 and P3 item needs something outside this branch: a backend action contract (D3-08, D3-09, D3-15),
official pages or a website fix (D3-21, D3-22), a real model provider (D3-16), another language (D3-17), or an
independent red team (D3-30). They are listed with owners in section 5.

## 2. Verification (17 Nov, after all fixes)

| Check | Result |
|---|---|
| Tests | 845 collected, 840 pass, 4 skipped; the one failure is `test_index_status_reports_unbuilt_index_by_default` (XICTEK module, expects an unbuilt index but the repository ships one; was 26 failures) |
| Release acceptance, grounded off and on | critical 25/25, major 6/6 (minor: known M-03 off, 1/1 on) |
| Safety suite v1.1, 4 configurations | CLEARED ×4 (43/43 · 36/36 · 8/8) |
| Multi-turn journeys / adversarial cases | 8/8 · 18/18 |
| Grounded transcripts | 19/19 |
| Probe questions previously passing | **16 of 16 unchanged**; of the 34 flagged on 5 Nov, 17 improved, 0 worse |
| Production freeze | `freeze_config.py --verify` OK |
| Router labelled sets | 192/201 (was 191) |

**End-to-end quality, 159 judged questions** (16 Nov → 17 Nov; Day 1 baseline in the matrix):

| Measure | 16 Nov | 17 Nov |
|---|---|---|
| Correct | 128 | **133** |
| Wrong (unrelated) citations | 9 | **3** |
| Citation precision | 0.863 | **0.931** |
| Held-out unrelated citations (120) | 3 | **1** |
| Held-out "must be empty" refused | 68/69 | **69/69** |
| Probe questions correct (20, judged) | 13 | **16** |
| Day 1 questions correct (19) | 17 | 17 |
| Lexical fallback: correct / unrelated (held-out) | 27 / 8 | 27 / 5 |
| Latency, knowledge p50 / p95 | 23.0 / 28.8 ms | 25.3 / 33.7 ms (target < 250) |
| Latency, account p50 / p95 | 8.3 / 12.0 ms | 8.5 / 10.6 ms (target < 150) |

## 3. What was closed

| ID | P | Defect | Fix | Evidence |
|---|---|---|---|---|
| D3-02, D3-03 | P0 | "How much does Ali owe me?" and "How much do I owe my suppliers?" returned the overall balance as that person's figure | U7 honest limit: "I can't see per-customer or per-supplier balances yet…", in English, Roman Urdu and Urdu | Q14, Q17; `test_u7_limits_*` |
| D3-28 | P0 | Own receivables questions refused as another person's data | Same U7 reply; the privacy guard is unchanged | Q15, Q16 |
| D3-04, D3-05 | P0, P1 | Month totals labelled "this week"; "by category" returned totals only | U7: states that only the current month and no category breakdown exist yet | Q21, Q22, Q23 |
| D3-07 | P1 | "Categorize: 1500 for printer ink" went to the no-source fallback | Office-supply words added to Shopping; the categorize flow answers | Q28 |
| D3-12 | P1 | "galti ho gayi, 450 nahi 540 tha" not recognised | Roman Urdu correction words added; gets the safe correction reply | Q08, router 192/201 |
| D3-14 | P2 | "Have you sent the payment to my customer?" cited an overdue-balance article | U7: "I can't send payments or messages, and I can't check whether one went out." | H-TC-08 |
| D3-27 | P2 | "Does HisabDo have a web version?" answered with the Android requirement | R13: a word the documentation never mentions → no-source reply | P-I27 |
| D3-29, E2E-09 | P1, P2 | "Why is my total wrong?" blocked, then sent to the correction flow | One clarifying question: which total, which period | Q50 |
| E2E-03 | P2 | "Can I send a customer their statement as a PDF?" refused by the third-party guard | Narrow exemption: product capability question, about customers, no relatives, ids or figures | `test_product_capability_exemption_is_narrow` |
| E2E-05 | P2 | Accountant sharing FAQ not retrieved for "Can my accountant see my expenses?" | Glossary entry | Q46 now cites the accountant FAQ |
| E2E-04 | P1 | Unrelated "related topic" answers for questions the KB cannot answer | R13: general bookkeeping blogs that never mention HisabDo are not evidence about the app. Unrelated citations on the 20 probe questions 6 → 2 | Partial; see section 5 |
| E2E-10 | P2 | The promotional block "Start Managing Your Finances" was still in the retrieval index (364 chunks against 363 records) and reached the context as an unrelated passage for 14 judged questions | Removed in the cleaner, KB, set and manifest rebuilt; vector checksum unchanged | Index 363; qrels updated |
| E2E-11 | P2 | `ingest_dept3.py --offline` rebuilt from the newest snapshot folder. A mistaken rebuild from the unreviewed 10 Nov site snapshot was caught by the sample check and reverted | Offline uses the approved snapshot named in the manifest | Rebuild reproduces checksum `e5e0cb7482e12318` |
| E2E-08 | P3 | 26 XICTEK test failures | Windows encoding bug (files read as cp1252); fixed in `vector_store.py` | 26 → 1 |
| D3-32 | P2 | Lexical fallback weaker than hybrid | Accepted as an operational control: `kb.degraded` alert, fastembed required, `KB_RETRIEVER_MODE=hybrid` in production | Runbook section 5 |
| D3-06, D3-23 | P1, P3 | Current month only; petty cash from blogs | Accepted: honest message / correct general guidance | |

Earlier in the same phase (13 to 16 Nov): D3-10, D3-13, D3-26, E2E-01, E2E-02, E2E-06.

### Formatting inconsistencies closed

| Inconsistency | Now |
|---|---|
| Limits and refusals worded differently per route (balance in place of a missing figure, boundary text, "demo data") | One structure for every limit: what cannot be done, why in one clause, what can be asked instead; one question at most; English, Roman Urdu, Urdu |
| Same paragraph repeated in consecutive turns | One-line short forms (U5) |
| Quoted excerpts of different lengths, a bullet list read as one 967-character sentence | Excerpts ≤ 450 characters at a word boundary; related-topic answers ≤ 2 sentences |
| Promotional filler in the index | Removed at source |
| Knowledge set (363) and retrieval index (364) disagreeing | Both 363, one source of truth, checked by the freeze |
| Source labels: new reply kinds had no route label | `limit_notice` and `escalation` are counted in metrics and alerts |

## 4. Retrieval edge cases

| Edge case | Handling | Result |
|---|---|---|
| Feature question the KB has no page for | R13 + R2 no-source reply, with the support contact | Bank connection, web version, edit, budget now no-source |
| General advice blog offered as evidence for an app feature | Dropped unless it mentions HisabDo | Unrelated citations 9 → 3 |
| Word the documentation never uses ("web", "recurring") | A neighbouring-topic passage is dropped | P-I27 |
| Conflicting sources and a shared common word ("support") | A conflicted passage needs the question's rare word | Q45 conflict kept; recurring-expenses question no longer shows the currency conflict |
| Definition question ("What does udhar mean?") | Answered, not clarified, in both retrieval modes | Lexical 27 correct |
| Synonym gap ("accountant see" vs "share with accountant") | Glossary | Q46 |
| Urdu script | Not closed | D3-31 |

## 5. Not closed, and why

| ID | P | Item | Why not closed | Owner | Next step |
|---|---|---|---|---|---|
| D3-01 | P0 | Backend is a mock | Needs the authenticated backend | Hassan Hussain | Connect; the isolation tests define the contract |
| D3-18, D3-19 | P1 | No official pages for add, edit, recategorize, receipts, budgets, recurring, multi-user | No source exists; the chatbot says so (no-source reply) | Mian Usman Khalid | Publish the pages, then ingest |
| D3-20 | P1 | Currency conflict (C-06) | The fact needs the owner; handling verified | Mian Usman Khalid | Confirm the list |
| D3-24, D3-25, D3-31 | P1 | Urdu script retrieval (3 held-out Urdu cases left) | English-only embeddings | Fahad Zubairi | Evaluate a multilingual model against the 159 questions |
| D3-11 | P1 | Two amounts in one message | Dialogue redesign | Saba Talat | Multi-item slot filling |
| E2E-04 | P1 | Remaining unrelated citations (add an expense, recurring) | Closes with D3-18, D3-19 | Fahad Zubairi | |
| E2E-07 | P1 | KB behind the live site (OFF-02, OFF-03 redesigned, OFF-01 not parseable) | Needs content-owner review of 21 new sections | Fahad Zubairi + content owner | Runbook section 3 |
| D3-08, D3-09, D3-15 | P2 | Supplier payment, udhar given, edit older entries | Need new entry types and entry ids in the action contract | Saba Talat, Hassan Hussain | Contract |
| D3-21 | P2 | Six sitemap pages not audited | Needs approval by the content owner | Fahad Zubairi | Audit, register, ingest |
| D3-22 | P2 | Broken blog links, stale counters | Website content | Mian Usman Khalid | Website owner |
| D3-16 | P3 | Real model provider not enabled | Needs a provider and key | Muhammad Hamza Nawaz | Run the same gates with it |
| D3-17 | P3 | Hindi and Arabic | Out of scope; documented | Fahad Zubairi + Saba Talat | After Urdu |
| D3-30 | P3 | Rules and attacks by one author | Needs another person | Syeda Isma Nazir | Red-team suite v1.2 |
| E2E-08 | P3 | One XICTEK test expects no index | Another team's test | XICTEK owner | Use a temporary index folder |

## 6. Risks at freeze

* Figures are demo data until D3-01. The chatbot says so and states each limit; it never presents another person's
  figure.
* The approved KB is the 27 Oct snapshot; the live site has moved on.
* No real model has been measured. The checks (`conversation_ux_eval.py`, `grounded_transcripts.py`) run unchanged when one is enabled.
