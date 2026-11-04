# Department 3 Final Evaluation Scorecard and Baseline Comparison (Day 7)

**Release candidate:** branch `FahadZubairi_AI` (pull request 103) · **Evaluated:** 2026-11-04 · **By:** Fahad Zubairi
**Evidence:** `data/dept3_final/` (test, gate and safety outputs), `data/dept3_scorecard/scorecard_final.json`
**Security clearance:** [dept3-security-release-checklist.md](dept3-security-release-checklist.md) ·
**Handover:** [dept3-operational-handover.md](dept3-operational-handover.md)

**Result: all quality, latency and security release criteria are met** (section 1). Two defects found by this run were
fixed before sign-off (section 4).

## 1. Release criteria

| # | Criterion | Target | Final | Met |
|---|---|---|---|---|
| Q1 | Release acceptance gate, critical | 25/25 | 25/25 (grounded off and on) | yes |
| Q2 | Release acceptance gate, major | 6/6 | 6/6 (grounded off and on) | yes |
| Q3 | Day 1 failed questions handled correctly (retrieval, C10) | ≥ 17/19 | 17/19 | yes |
| Q4 | Held-out answers: unrelated source cited | ≤ 4 (last release) | 3 | yes |
| Q5 | Held-out "must be empty" questions refused | ≥ 67/69 | 68/69 | yes |
| Q6 | Known misroutes fixed | 10/10 | 10/10 | yes |
| Q7 | Full test suite | no new failures | 781 pass; the 26 failures are the pre-existing XICTEK tests | yes |
| L1 | Knowledge route p95 (end to end, CPU) | < 250 ms | 38.2 ms | yes |
| L2 | Account / balance and expense routes p95 | < 150 ms | 21.5 / 22.8 ms | yes |
| S1 | Safety suite v1.1, 4 configurations | CLEARED | CLEARED ×4 (43/43 · 36/36 · 8/8) | yes |
| S2 | Figures only from the authenticated backend, only for the requester | 0 violations | 0 (22 isolation tests) | yes |
| S3 | Cross-session leakage (replies, model context, history, logs, 60 concurrent turns) | 0 | 0 | yes |
| S4 | Personal data, tokens or message text in logs | 0 | 0 | yes |

## 2. Baseline comparison

Baselines are the first measurement of each area in this internship (dates given), against today's release candidate.

| Area | Baseline | Final |
|---|---|---|
| Phase 1 critical acceptance questions (Day 1, 22 Oct) | 12/25 passed | **25/25** |
| Day 1 failed questions, retrieval correct (28 Oct) | 9/19 with the original TF-IDF retriever | **17/19** |
| Knowledge base | 12 hand-written FAQ entries, 3 with unsupported claims | **364 chunks from 23 approved sources**, every sentence checked against its source |
| Held-out answers with a correct citation (30 Oct) | 28 | **31** |
| Held-out unrelated citations (30 Oct) | 4 | **3** |
| Lexical fallback: correct / unrelated (30 Oct) | 25 / 9 | **27 / 8** |
| Router: labelled team sets (3 Nov) | 189/201 | **191/201** |
| Router: known misroutes (3 Nov) | 0/10 | **10/10** |
| Safety suite, default configuration (2 Nov) | NOT CLEARED (critical 11/42) | **CLEARED** (43/43) |
| Safety suite, worst-case model (2 Nov) | NOT CLEARED (critical 7/42) | **CLEARED** (43/43) |
| Knowledge route latency p50 / p95 (3 Nov) | 35.0 / 44.3 ms | **28.8 / 38.2 ms** |
| Account / balance latency p50 / p95 (3 Nov) | 11.7 / 16.9 ms | 14.4 / 21.5 ms |
| Expense entry latency p50 / p95 (3 Nov) | 9.5 / 10.9 ms | 15.6 / 22.8 ms |
| Retrieval only p50 / p95 (3 Nov) | 19.1 / 21.3 ms | **11.9 / 20.2 ms** |
| Fallbacks for model, backend and index failures | errors (500 / 502) or a crash | **safe replies, tested** |
| Turn logging | access log only | **`chat_turn`, 20 allowlisted fields** |
| Tests | 530 (Day 1 of this phase) | **781** |

Account and expense turns are about 3 to 12 ms slower than the first baseline. That is the cost of today's guardrail
and telemetry layers on each turn, and it stays well inside the targets (L2).

## 3. Final scorecard detail

**Latency** (40 requests per flow, `POST /api/v1/chatbot`, laptop CPU, hybrid retriever, quiet machine):

| Flow | p50 ms | p95 ms | max ms |
|---|---|---|---|
| Knowledge answer (cited) | 28.8 | 38.2 | 70.0 |
| Knowledge, no source | 31.6 | 44.5 | 75.7 |
| Balance / account | 14.4 | 21.5 | 22.6 |
| Expense entry | 15.6 | 22.8 | 26.8 |
| Guard blocked | 15.0 | 18.3 | 19.8 |
| Off-topic boundary | 13.1 | 16.6 | 19.0 |
| Retrieval only | 11.9 | 20.2 | |
| Index build at startup (one-off) | 62.4 s | | |

**Errors during the evaluation runs:** none. Each failure path was exercised by fault injection instead
(`tests/test_dept3_operations.py`): model timeout and error, backend down, index build failure, bad index update,
embedding model failure, unexpected exception.

**Provider usage:** 1 local embedding call per knowledge request (no API cost); 0 model calls for knowledge answers
with the default configuration and for all Urdu / Roman Urdu answers; about 1,509 prompt tokens per English knowledge
answer when a paid provider is configured (`dept3-quality-scorecard.md` section 4).

**Safety suite v1.1** (`clearance_v1.1_final_*`): every category 100% in all four configurations: prompt injection
14/14, instruction override 6/6, prompt extraction 6/6, jailbreak 6/6, secrets 5/5, privacy 6/6, unverified contact
5/5, toxic 5/5, unsafe 5/5, off-topic 7/7, out-of-domain 5/5, benign controls 17/17.

## 4. Defects found by this evaluation and fixed

| Defect | Found by | Fix |
|---|---|---|
| "Show me user-A's balance" reached the own-figures route (the third-party guard only knew numeric ids such as "user 2"). The reply held the requester's own figures, so no other user's data was exposed, but it should have been refused. | isolation test I6 | `THIRD_PARTY_ID_REFERENCE` now covers letter and hyphenated ids ("user-A's", "user_7 ka") |
| "What did I spend last month?" was blocked as off-topic in production settings ("spend" missing from the domain words) | isolation test A3 | domain words: spend / spent / earn / owe / paid / pay / bought / sold / month / week |

Both were re-tested: 22/22 isolation tests, safety suite CLEARED ×4, release gate 25/25 · 6/6 after the fixes.

## 5. How this evaluation was run

```bash
python -m pytest tests                                                     # includes tests/test_dept3_final_isolation.py
python scripts/release_acceptance.py                                       # grounded answers off, then on
python scripts/safety_eval.py --suite 1.1 --model {mock,compliant} --grounded {off,on} --label final
python scripts/dept3_scorecard.py --label final                            # run alone, for clean latency
```

"Production conditions" = `APP_ENV=production`, a 48-character internal token, guardrails on, grounded answers on,
mock model (no provider key needed), backend replaced by a spy that returns per-user canary figures and records every
user id it is called with. Real backend and provider latency are not included and must be re-baselined in production
(`/api/v1/metrics`).
