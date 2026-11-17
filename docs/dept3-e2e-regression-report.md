# Department 3 End-to-End Regression Report

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-16 · **Branch:** `FahadZubairi_AI`
**Runner:** `scripts/e2e_regression.py` → `data/dept3_e2e/e2e_results.json` · **Evidence:** `data/dept3_e2e/`
**Companion documents:** [Before-vs-After Matrix](dept3-before-after-matrix.md) · [Final Defect Triage Log](dept3-final-defect-triage-log.md)

## 1. Verdict

**Zero regression on previously passing cases, and measurable improvement over the Day 1 baseline.** The run found and
fixed **3 regressions or false blocks** before sign-off (section 5). It also confirmed what is **not** solved:
feature questions the knowledge base has no page for, and the mock account backend. Those are listed in the triage log
with owners.

| Question | Answer |
|---|---|
| Any previously passing case now failing? | **No.** 16 of 16 previously passing probe questions give the same reply. The 9 Day 1 questions that passed in the Day 1 baseline still pass. 139 of 139 judged questions are as good or better than the 4 Nov release candidate |
| Source attribution accurate? | 86.3% of the passages cited across 159 judged questions are relevant; 11 unrelated citations; 0 on the Day 1 questions; the 19 verified grounded transcripts pass every citation, link and support check |
| Financial privacy boundaries held? | **Yes.** 0 leaks in 4 safety-suite configurations (87 cases each), 18 further adversarial cases, 22 isolation tests. No data for anyone but the requester |
| Latency within target? | **Yes.** Knowledge route p50 / p95 23.0 / 28.8 ms (target p95 < 250 ms); account 8.3 / 12.0 ms (target < 150 ms) |
| Overall improvement over Day 1 | Day 1 questions 9/19 → **17/19**; acceptance gate 12/25 → **25/25**; safety suite not cleared → **cleared**; retrieval correct 62.6% → **86.3%** |

## 2. What was run

Pipeline under test: cleaned KB (364 chunks, 23 sources) → hybrid retrieval (bge-small + BM25, threshold 0.566273, top 2)
→ router gate → grounded answers (R1–R12) → conversation rules (U1–U6) → guardrails, through
`POST /api/v1/chatbot` with the mock model and mock backend, the same settings as the 5 Nov probe.

| # | Suite | Size | Result |
|---|---|---|---|
| 1 | Day 1 golden set (the 19 Phase 1 failed questions), end to end | 19 | **17 correct**, 2 safe no-answers, 0 wrong citations (baseline 9) |
| 2 | Held-out judged set, end to end | 120 | 98 correct (30 answered with the right source, 68 correctly refused), 19 safe no-answers, 3 unrelated citations |
| 3 | Failed-query benchmark (19 Day 1 + 20 judged probe questions) | 39 | 14 correct, 9 unrelated citations: the hard set, see section 4 |
| 4 | Phase 2 Day 1 probe, replayed (50 expense-management questions) | 50 | **16/16 previously passing unchanged**; of the 34 flagged on 5 Nov, 7 changed (4 improved, 3 other failures) |
| 5 | Multi-turn financial and product journeys | 8 journeys, 22 turns | **8/8 verified** (first run 4/8) |
| 6 | Adversarial and prompt-injection probes | 18 (7 multi-turn) + suite v1.1 (87) × 4 configurations | **18/18 held; CLEARED ×4** (critical 43/43, major 36/36, minor 8/8) |
| 7 | Release acceptance gate, grounded off and on | 32 each | Critical 25/25, major 6/6 in both; minor 0/1 off (known M-03, a concept question), 1/1 on |
| 8 | Grounded transcripts (citations, conflicts, ambiguity, fallbacks) | 19 | **19/19 verified** |
| 9 | Router labelled sets | 201 | 191/201 (unchanged); known misroutes 10/10 |
| 10 | Test suite | 839 | 809 pass, 4 skipped; 26 fail, all in the separate `xictek_website_assistant` module, the same 26 as before this phase |

## 3. Regression analysis

| Comparison | Method | Result |
|---|---|---|
| Day 1 baseline (28 Oct, original TF-IDF over 12 hand-written FAQ entries) | The 19 Day 1 questions, row by row | **0 regressions**, 8 improved (D01, D02, D03, D11–D15); 9 → 17 correct |
| 4 Nov release candidate | 139 judged questions, per-question grade through the grounded layer | **0 worse, 0 better**: identical, including after the 12 and 13 Nov changes |
| 5 Nov probe (Phase 2 Day 1) | 50 questions replayed, reply compared | **0 of 16 previously passing changed.** Of 34 flagged: Q33, Q43, Q44, Q48 fixed; Q45 unchanged (conflict kept after the fix in section 5); Q30, Q46, Q50 changed but still failing differently (below) |
| Failed-query benchmark | Probe questions judged against the source pool | 10 → 12 good of the 18 comparable questions (5 + 5 → 7 + 5) |

The three flagged questions that changed without being fixed:

| Q | Before (5 Nov) | After (16 Nov) | Assessment |
|---|---|---|---|
| Q30 "How do I edit an expense entry?" | Related-topic answer from "Use Technology to Reduce Friction" | Related-topic answer from "Expense Reports: What to Include" | Neutral: no edit page exists (D3-18); both unrelated |
| Q46 "Can my accountant see my expenses?" | Demo balance figures | Knowledge route, but an unrelated category guide is cited | The privacy answer exists in the KB but is not retrieved (E2E-05); a wrong figure has become a wrong citation, and neither claims a fact about the user's accountant |
| Q50 "Why is my total wrong?" | Blocked as off-topic | Handled by the correction flow ("I can only change entries confirmed in this chat") | Not blocked any more; still not a good answer (E2E-09) |

## 4. Quality, attribution and privacy results

**Source attribution** (end to end, 159 judged questions; qrels in `data/retrieval_eval/`):

| Set | Questions | Correct | Cited passages | Citation precision | Unrelated citations | Answer recall |
|---|---|---|---|---|---|---|
| Day 1 (19) | 19 | 17 | 9 | **1.000** | **0** | 0.714 (5 of 7) |
| Held-out (120) | 120 | 98 | 49 | 0.898 | 5 | 0.588 |
| Failed set (39) | 39 | 14 | 38 | 0.763 | 9 | 0.276 |
| Probe, judged (20) | 20 | 13 | 22 | 0.727 | 6 | 0.636 |
| **All (159)** | 159 | **128** | 80 | **0.863** | 11 | 0.609 |

Citation precision is the share of cited passages judged relevant; answer recall is the share of answerable questions
whose answering passage was cited. The failed set stays hard because most of its feature questions (edit an expense,
budget, recurring entries, receipts) have **no official page**: the rules turn some of them into safe replies (Q38 and the bank question are
no-source fallbacks; Q31, Q32, Q35 cite only background passages), but a neighbouring blog still scores above the
threshold for others (Q29, Q30, Q34, Q37).
This is E2E-04: closing it needs the pages (D3-18, D3-19), not more tuning; the strategy matrix shows every retrieval
option trades recall for precision.

**Privacy boundaries.**

| Check | Result |
|---|---|
| Other people's data (relatives, "user 1042", "I am the admin", multi-turn "and my brother?") | Refused every time (AX-13, AX-14, suite v1.1) |
| Figures only from the authenticated backend, only for the requester | 22 isolation tests pass; 0 violations |
| Cross-session leakage (replies, model context, history, logs, 60 concurrent turns) | 0 |
| Card number, CNIC, password typed by the user | Never repeated back (AX-10 to AX-12) |
| System prompt, service token, API keys | 0 in any reply, including with a worst-case model that obeys every injection |
| False refusals (safe direction) | Q15, Q16 (own receivables) and "send a customer their statement" are refused as third-party data: D3-28, E2E-03, kept open on purpose, see section 6 |

## 5. Defects found by this run and fixed

| ID | Found by | Defect | Fix | Test |
|---|---|---|---|---|
| E2E-01 | Probe replay | **My 13 Nov conflict rule dropped the currency conflict** (Q45): the reply cited an unrelated "how often should I record expenses" passage | A conflicted passage needs the question's rare word ("currencies"); with none, it must cover half the question | `test_conflict_survives_*`, `test_unrelated_question_does_not_become_a_conflict_notice` |
| E2E-02 | Full API vs harness | Urdu "how do I save a statement as PDF" blocked as off-topic since 3 Nov (domain list lacked the Urdu words) | Urdu domain words added | `test_urdu_pdf_statement_*` |
| E2E-06 | Lexical mode | "What does udhar mean?" became a clarifying question after my 12 Nov change: lexical held-out answers 27 → 25 | Definition questions are answered | `test_definition_question_is_answered_*` |

These were invisible to the earlier checks: the 13 Nov work was verified on the 139-question harness and the transcripts,
which did not contain the currency question end to end or run the lexical mode. The run now covers both.

## 6. Decisions in this run

* **The privacy guard was not loosened.** Q15, Q16 and the "their statement" refusal are false refusals, but they are
  on the safe side of a guard hardened against real attacks. Changing it belongs in a red-team-reviewed change
  (D3-28, E2E-03), not in a validation run.
* **Retrieval parameters were not retuned.** The strategy matrix of 11 Nov already shows the configuration is the best
  measured; no result here moves it.
* **Latency is reported with its noise.** On this laptop the same 120 knowledge requests gave p50 22.5 ms and 34.0 ms
  in two runs minutes apart (p95 31.9 and 47.8 ms; one earlier busy-machine run reached 89.6 ms). All are far inside
  the 250 ms target; the quiet-machine scorecard is used in the matrix.

## 7. Sign-off position

| Area | Status |
|---|---|
| Knowledge pipeline (KB, chunking, retrieval, grounding, citations, UX, guardrails) | **Passes validation.** No regression, no leak, targets met |
| Account figures | **Not production-ready:** backend is a mock (D3-01 to D3-04, D3-28, 5 open P0) |
| Knowledge base freshness | **Needs action:** live site changed since 27 Oct (E2E-07) |
| Feature coverage | **Content gap:** no official pages for edit, budget, recurring, receipts, multi-user (D3-18, D3-19) |

Open items by priority: P0 5 · P1 14 · P2 11 · P3 4 (41 entries, 9 of them found by this run; 6 fixed or closed). See the
[triage log](dept3-final-defect-triage-log.md).

## 8. Reproduce

```bash
python scripts/e2e_regression.py                # probe replay, 159 judged questions, attribution metrics
```
```bash
python scripts/conversation_ux_eval.py          # 8 journeys, 18 adversarial cases
```
```bash
python scripts/safety_eval.py --suite 1.1 --all # suite v1.1, 4 configurations
```
```bash
python scripts/dept3_scorecard.py --label e2e   # router, answers, latency
```
