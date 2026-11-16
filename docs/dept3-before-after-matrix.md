# Department 3 Before-vs-After Quality & Latency Benchmark Matrix

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-16 · **Branch:** `FahadZubairi_AI`
**Evidence:** `data/dept3_e2e/e2e_results.json`, `data/dept3_scorecard/scorecard_{before,final,e2e}.json`,
`data/retrieval_eval/results/`, `data/dept3_e2e/` · **Report:** [dept3-e2e-regression-report.md](dept3-e2e-regression-report.md)

"Before" is the first measurement of each area in this internship (date given). "After" is 16 Nov, the integrated
Phase 2 pipeline, on the same machine and settings (mock model, mock backend, hybrid retriever).

## 1. Quality

| Measure | Before | After | Change |
|---|---|---|---|
| **Day 1 failed questions, handled correctly** (19; 28 Oct baseline: original TF-IDF, 12 hand-written FAQ entries) | 9/19 | **17/19** | +8, 0 regressions |
| Day 1 answerable questions answered with the right source (7) | 1/7 | **5/7** | +4 (2 safe no-answers) |
| Day 1 answers that served wrong content | 6 (2 unrelated passages, 2 KB definitions instead of own figures, 1 false claim served as fact, 1 inaccurate source text) | **0** | every sentence is now checked against its source |
| **Retrieval correct, 139 judged questions** (TF-IDF algorithm on the new KB → final pipeline, retrieval only) | 87 (62.6%) | **120 (86.3%)** | +33 |
| Answer recall@2 (answering passage reaches the context) | 0.121 | **0.724** | ×6 |
| MRR | 0.459 | **0.732** | +0.273 |
| Context precision (relevant share of passages sent) | 0.818 | **0.908** | +0.090 |
| Unrelated passages sent (of passages sent) | 2 of 11 | 9 of 98 | more passages sent, a smaller share unrelated |
| Held-out answers with a correct citation (30 Oct → 16 Nov, grounded layer) | 28 | **31** | +3 |
| Held-out unrelated citations (30 Oct → 16 Nov) | 4 | **3** | −1 |
| Held-out "must be empty" questions refused (grounded layer) | 69/69 on 30 Oct | 68/69 | H-TC-08 cites an unrelated article since the 3 Nov router change; open as D3-14 |
| Lexical fallback: correct / unrelated (30 Oct → 16 Nov) | 25 / 9 | **27 / 8** | +2 / −1 |
| **End-to-end attribution, 159 judged questions** (new measure) | n/a | citation precision **0.863**, 11 unrelated, 128 correct (80.5%) | |
| Phase 2 probe, 18 comparable judged questions (5 Nov → 16 Nov replies) | 10 good, 4 wrong citations | **12 good**, 5 wrong citations | +2 good; Q46 became a wrong citation (E2E-05) |
| Phase 2 probe, previously passing (16) | 16 | **16 unchanged** | 0 regressions |
| Phase 2 probe, flagged on 5 Nov (34) | 34 weak or failed | 4 fixed (Q33, Q43, Q44, Q48), 3 changed and still failing, 27 unchanged | see triage log |
| **Multi-turn journeys verified** (8 journeys, 22 turns; first run 13 Nov) | 4/8 | **8/8** | |
| Adversarial cases held (18; first run 13 Nov) | 16/18 | **18/18** | |
| Grounded transcripts verified (first run 12 Nov) | 12/19 | **19/19** | |

## 2. Safety, acceptance and tests

| Measure | Before | After |
|---|---|---|
| Phase 1 critical acceptance questions (22 Oct → 16 Nov) | 12/25 | **25/25** (grounded off and on), major 6/6 |
| Safety suite v1.1, default configuration (2 Nov → 16 Nov) | NOT CLEARED, critical 11/42 | **CLEARED**, critical 43/43, major 36/36, minor 8/8 |
| Safety suite v1.1, worst-case model that obeys every attack | NOT CLEARED, critical 7/42 | **CLEARED** ×2 grounded settings, same counts |
| Safety suite, all 4 configurations | n/a | **CLEARED ×4** |
| Router: labelled team sets | 189/201 (3 Nov) | **191/201** |
| Router: known misroutes | 0/10 | **10/10** |
| Fallbacks for model, backend or index failure | errors (500, 502) or a crash | **safe replies, tested** |
| Turn logging | access log only | `chat_turn`, 20 allowlisted fields, no message text |
| Tests passing | 530 (start of Phase 2) | **809** (+26 pre-existing failures in the separate XICTEK module) |
| Source knowledge | 12 hand-written FAQ entries, 3 with unsupported claims | 364 chunks from 23 approved official pages, every sentence checked against its source |

## 3. Latency (milliseconds, POST /api/v1/chatbot, laptop CPU, 40 requests per flow)

Quiet-machine scorecard (`dept3_scorecard.py`, same method on all three dates):

| Flow | Before (3 Nov) p50 / p95 | Day 7 (4 Nov) p50 / p95 | **After (16 Nov) p50 / p95** | Target p95 | Met |
|---|---|---|---|---|---|
| Knowledge answer (hybrid retrieval + grounding) | 35.0 / 44.3 | 28.8 / 38.2 | **23.0 / 28.8** | < 250 | yes |
| Knowledge, no source (fallback) | 34.9 / 40.8 | 31.6 / 44.5 | **25.0 / 33.2** | < 250 | yes |
| Account / balance | 11.7 / 16.9 | 14.4 / 21.5 | **8.3 / 12.0** | < 150 | yes |
| Expense entry | 9.5 / 10.9 | 15.6 / 22.8 | **6.8 / 8.8** | < 150 | yes |
| Guardrail block | 6.2 / 8.1 | 15.0 / 18.3 | **5.8 / 7.3** | n/a | |
| Off-topic boundary | 7.5 / 10.9 | 13.1 / 16.6 | **6.3 / 7.8** | n/a | |
| Retrieval only | 19.1 / 21.3 | 11.9 / 20.2 | **10.8 / 14.2** | n/a | |

Other measurements on 16 Nov (same machine):

| Measurement | p50 | p95 | Note |
|---|---|---|---|
| Knowledge, 40 varied held-out questions (longer, mixed languages) | 32.8 | 42.9 | `e2e_regression.py` |
| Knowledge, 120 requests, three consecutive runs | 22.5 / 34.0 | 31.9 / 47.8 | the machine is noisy; one busy run reached p95 89.6 ms |
| Day 1 path (legacy TF-IDF over the old FAQ file, grounded answers off) | 7.0 | 9.9 | the cost of retrieval quality: about 15 to 27 ms per knowledge question |
| Account, expense, small talk, guardrail (e2e run) | 10.5 / 8.8 / 9.4 / 7.9 | 13.7 / 10.6 / 12.8 / 11.5 | |

Latency never exceeds a target in any run. The knowledge route is about 3 to 5× slower than the Day 1 TF-IDF path (7 ms) and
the retrieval it runs has a 6× higher answer recall (0.121 → 0.724); with a real model the generation time (hundreds of milliseconds to seconds) dominates, not
retrieval.

## 4. Strategy comparison summary (from the 11 Nov matrix)

| Strategy | Calibration correct /139 | Failed set /39 | Unseen probe /20 | ms / query |
|---|---|---|---|---|
| Dense vector only (Day 1 style) | 98 | 13 | 9 | 32 |
| Hybrid + rewrite + router gate (**final**) | **120** | 9 | 9 | 23 |
| + metadata filter | 120 | 10 | 7 | 21 |
| + cross-encoder rerank | 118 | 12 | 5 | 1057 |

The final configuration was re-validated end to end today and was not changed.

## 5. What did not improve

| Area | Before | After | Why |
|---|---|---|---|
| Failed-set answer recall (feature how-to questions) | low | 0.276 | The KB has no official pages for these questions (D3-18, D3-19); retrieval cannot find what is not there |
| Account figures | demo data | demo data | Backend is a mock (D3-01 to D3-04) |
| Urdu script questions | weakest language | 9 correct, 7 safe, 1 unrelated of 17 answerable | English-only embeddings (D3-31) |
| Held-out unrelated citations | 4 | 3 | The 3 left are retrieval misses |
