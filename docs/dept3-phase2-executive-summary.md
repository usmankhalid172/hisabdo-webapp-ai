# Department 3 Phase 2 Final Executive Summary Report

**Project:** HisabDo expense management chatbot (AI service) · **Prepared by:** Fahad Zubairi, AI intern · **Date:** 2026-11-18
**Branch:** `FahadZubairi_AI` (pull request 103) · **Status:** ready for handover, with the conditions in section 6

## 1. Summary for decision makers

The chatbot's knowledge pipeline is complete, tested and frozen. It now answers product questions only from verified
HisabDo pages, shows the source of every answer, says plainly when it does not know, keeps a multi-turn conversation
without repeating itself, refuses unsafe or private requests, and sends account problems to human support.

| | Day 1 (22 to 28 Oct) | Day 9 (18 Nov) |
|---|---|---|
| Critical acceptance questions passed | 12 of 25 | **25 of 25** (and 6 of 6 major) |
| The 19 questions that failed on Day 1 | 9 correct | **17 correct**, 0 lost |
| Answers with a visible source | none | **every knowledge answer** |
| Judged questions answered correctly | 62.6% (original algorithm) | **86.3%** (retrieval), **83.6%** end to end (133 of 159) |
| Cited sources that were relevant | not measured | **93.1%** |
| Safety and privacy suite | **not cleared** (critical 11 of 42) | **cleared in all 4 configurations** (43 of 43 critical) |
| Knowledge base | 12 hand-written entries, 3 with unsupported claims | 363 chunks from 23 official pages, every sentence checked against its source |
| Response time, knowledge questions (p95) | 44 ms | **34 ms**, target under 250 ms |
| Automated tests | 530 | **840 passing** |

**What is not done:** the account backend is still a stand-in that returns the same demo figures for everyone, and
official help pages do not exist for several expense features (edit, budget, recurring, receipts, multi-user). The
chatbot states these limits honestly instead of guessing. They are the main Phase 3 items (section 7).

## 2. What Phase 2 delivered

| Area | Delivered | Evidence |
|---|---|---|
| Cleaned knowledge base | 23 approved official sources, 286 UI and page blocks purged, standardized records with a schema and a verified sample | [dept3-knowledge-set.md](dept3-knowledge-set.md) |
| Chunking and ingestion | Chunk sizes measured per content type; repeatable ingestion with failed-page, duplicate and vector-error capture; a checklist and execution reports | [dept3-chunking-embedding-config.md](dept3-chunking-embedding-config.md), [dept3-ingestion-master-checklist.md](dept3-ingestion-master-checklist.md) |
| Retrieval | 10 strategies compared on the Day 1 failed set; hybrid keyword plus vector search with a router gate chosen | [dept3-retrieval-strategy-matrix.md](dept3-retrieval-strategy-matrix.md) |
| Grounded answers and citations | Rules R1 to R13: cite only what supports, show every source link, show conflicts, ask one clarifying question, never guess | [dept3-grounded-rulebook.md](dept3-grounded-rulebook.md) |
| Conversation quality and safety | Rules U1 to U7: context across turns, no repeated paragraphs, human-support escalation, honest limits; 18 adversarial cases | [dept3-conversation-ux-rulebook.md](dept3-conversation-ux-rulebook.md), [dept3-adversarial-test-log.md](dept3-adversarial-test-log.md) |
| Validation and closure | End-to-end regression with zero regressions; defect triage log (43 entries); closure pass | [dept3-e2e-regression-report.md](dept3-e2e-regression-report.md), [dept3-final-defect-closure-report.md](dept3-final-defect-closure-report.md) |
| Production package | Frozen configuration with a verification test; operations runbook | [dept3-production-config-freeze-spec.md](dept3-production-config-freeze-spec.md), [dept3-operations-runbook.md](dept3-operations-runbook.md) |
| Handover | Live demonstration (23 of 23 steps verified), checklist, sign-off package | [dept3-live-demo-checklist.md](dept3-live-demo-checklist.md), [dept3-handover-signoff-package.md](dept3-handover-signoff-package.md) |

## 3. Day 1 versus Day 9 benchmark matrix

Quality (sources: `data/retrieval_eval/results/`, `data/dept3_e2e/`, [before-after matrix](dept3-before-after-matrix.md)).

| Measure | Day 1 baseline | Day 9 | Change |
|---|---|---|---|
| Day 1 failed questions handled correctly (19) | 9 | 17 | +8 |
| Day 1 answerable questions answered with the right source (7) | 1 | 5 | +4 |
| Retrieval correct, 139 judged questions (retrieval only) | 87 (62.6%) | 120 (86.3%) | +33 |
| Answer reaches the model (recall) | 0.121 | 0.724 | ×6 |
| Relevant share of passages sent | 0.818 | 0.908 | +0.090 |
| End to end, 159 judged questions | not available | 133 correct, 3 unrelated citations, citation precision 0.931 | |
| Previously passing probe questions (16) | 16 | 16 unchanged | no regression |
| Probe questions flagged weak on 5 Nov (34) | 34 | 17 improved, 0 worse | |
| Held-out unrelated citations (120) | 4 (30 Oct) | 1 | −3 |
| Router, labelled sets (201) | 189 | 192 | +3 |
| Router, known misroutes | 0 of 10 | 10 of 10 | |
| Multi-turn journeys verified (first run 13 Nov) | 4 of 8 | 8 of 8 | |
| Adversarial cases held (first run 13 Nov) | 16 of 18 | 18 of 18 | |

Safety, latency and operations:

| Measure | Day 1 baseline | Day 9 |
|---|---|---|
| Safety suite, default configuration | not cleared, critical 11 of 42 | cleared, critical 43 of 43, major 36 of 36, minor 8 of 8 |
| Safety suite, worst-case model that obeys every attack | not cleared, critical 7 of 42 | cleared ×2 settings |
| Critical safety cases failed | 31 of 42 failed on 2 Nov | 0 in any run |
| Latency knowledge p50 / p95 | 35.0 / 44.3 ms (3 Nov) | 25.3 / 33.7 ms |
| Latency account p50 / p95 | 11.7 / 16.9 ms | 8.5 / 10.6 ms |
| Failure of model, backend or index | errors (500, 502) or a crash | safe replies, tested |
| Logging | access log only | 20 allowlisted fields, no message text |
| Defects in the triage log | 32 found on Phase 2 Day 1 | 22 fixed, 3 accepted, 18 open or partial (P0: 1) |

## 4. Live demonstration result

The demonstration ran against the service with the frozen production settings (`scripts/live_demo.py`): **23 of 23
steps verified.** The full transcript is [dept3-live-demo-transcript.md](dept3-live-demo-transcript.md); the checklist
for stakeholders is [dept3-live-demo-checklist.md](dept3-live-demo-checklist.md).

Examples, Day 1 against now (same question):

| Question | Day 1 path | Now |
|---|---|---|
| "Are my expense records synced to the cloud?" | Showed the demo balance and totals | Answers from the Privacy Policy with its section and link |
| "Can my accountant see my expenses?" | Showed the demo balance and totals | Cites the "share reports with my accountant" FAQ |
| "Which currencies can I record expenses in?" | Customer profile text, unrelated | Says the official sources disagree, shows all three versions, flags it for review |
| "Can I connect HisabDo to my bank account?" | Unrelated generic message | "I couldn't find this in HisabDo's official help pages, so I won't guess", with the support contact |
| "How much does Ali owe me?" | Overall balance as Ali's debt | "I can't see per-customer balances yet…" |

## 5. Frozen production configuration and operations

* **Configuration:** hybrid retrieval (0.6 vector + 0.4 keyword), relevance threshold 0.566273, top 2 passages, margin
  0.05, exact in-memory index of 363 vectors (384 dimensions), embedding model file hash recorded, prompts and rule files hashed.
  `scripts/freeze_config.py --verify` and `tests/test_config_freeze.py` fail the build on any change. Details:
  [freeze spec](dept3-production-config-freeze-spec.md).
* **Operations:** deployment gate and smoke test, 30-day knowledge update, index rebuild, 15 monitoring alerts,
  rollback for code, knowledge base and settings, incident procedures: [runbook](dept3-operations-runbook.md).
* **Required setting:** `GROUNDED_ANSWERS_ENABLED=true` (the code default is false).

## 6. Conditions on the handover

1. **Demo figures.** Account figures come from a stand-in backend until D3-01 is done. Do not present them as real.
2. **Knowledge snapshot.** The approved knowledge base is the 27 Oct snapshot. The live site was redesigned after it;
   update with the runbook procedure and the content owner before relying on newer pages (E2E-07).
3. **No real model.** Answers are extractive. A real model must pass the same gates before it is enabled.
4. **Release tag.** The freeze tag `dept3-freeze-v1.0` still has to be created by a release owner.
5. **One stale test** in the separate XICTEK module expects no search index; its owner needs to change it.

## 7. Open backlog and Phase 3 recommendations

| # | Item | Why it matters | Owner | Size |
|---|---|---|---|---|
| 1 | **Connect the authenticated backend** (D3-01): real figures, per-customer and per-supplier balances, month and week periods, category totals | Removes the demo-data limit; five P0 and P1 limits depend on it | Hassan Hussain | Large |
| 2 | **Publish official help pages** for add, edit and recategorize an expense, receipts, budgets, recurring entries, multi-user (D3-18, D3-19), and settle the currency list (D3-20) | These questions get "not found" today; retrieval cannot find what does not exist | Mian Usman Khalid | Medium |
| 3 | **Refresh the knowledge base from the live site** (E2E-07): update the FAQ cleaner, review 21 new sections, schedule the 30-day ingestion | The approved snapshot is 3 weeks old | Fahad Zubairi + content owner | Small |
| 4 | **Urdu script retrieval** (D3-31, D3-24, D3-25): evaluate a multilingual embedding model on the 159 judged questions | Weakest language: 9 correct, 7 safe, 1 unrelated of 17 | Fahad Zubairi | Medium |
| 5 | **Entry types in the dialogue**: udhar given, supplier payments, two amounts in one message, edit older entries (D3-08, D3-09, D3-11, D3-15) | Needs the action contract extended | Saba Talat, Hassan Hussain | Medium |
| 6 | **Enable a real model provider** (D3-16) behind the same gates; add a 40-answer wording review | Wording quality is unmeasured | Muhammad Hamza Nawaz | Medium |
| 7 | **Independent red-team suite v1.2** (D3-30) written by another person | Rules and attacks have one author | Syeda Isma Nazir | Small |
| 8 | **Wire the gates into CI**: freeze verify, acceptance, safety suite, e2e regression on every pull request | Makes the freeze enforceable without a person | Platform | Small |
| 9 | **Production feedback loop**: thumbs on answers, weekly sample of `kb_fallback` questions, add judged questions | Real questions replace the probe set | Fahad Zubairi + QA | Medium |
| 10 | **Hindi and Arabic** (D3-17): glossary, router cues, guard patterns, judged questions | Supported by the app, not by the chatbot | Fahad Zubairi + Saba Talat | Medium |
| 11 | **Website content** (D3-22, D3-21): broken blog links, stale counters, six unaudited pages | Source quality | Mian Usman Khalid | Small |
| 12 | **Re-test reranking** after the new pages exist | It fixed 7 of the 19 hardest questions but cost 1 s per query | Fahad Zubairi | Small |

## 8. Risks

| Risk | Likelihood | Effect | Control |
|---|---|---|---|
| Users read demo figures as real | Medium until item 1 | Wrong decisions | Replies say "demo data"; do not expose to real users before item 1 |
| Website changes make answers stale | High | Wrong product facts | Item 3, 30-day schedule, stale-knowledge alert |
| A real model words things loosely | Medium | Unsupported claims | Item 6: sentence-level support check already enforces sources |
| Guard rules miss a new attack | Medium | Leak or misuse | Item 7, suite versioning, leak alert and incident procedure |

## 9. Conclusion

Phase 2 meets its goals for the knowledge pipeline: measurably more accurate, every answer sourced, safe on private
data, stable across turns, and frozen with a repeatable way to maintain it. Handover is recommended with the five
conditions in section 6. Formal sign-off: [dept3-handover-signoff-package.md](dept3-handover-signoff-package.md).
