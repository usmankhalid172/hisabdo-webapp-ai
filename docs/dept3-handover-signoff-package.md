# Department 3 Formal Handover Sign-Off Package

**Project:** HisabDo expense management chatbot, Phase 2 · **Date:** 2026-11-18
**From:** Fahad Zubairi (AI intern) · **Branch:** `FahadZubairi_AI` (pull request 103)
**Status of signatures: not yet signed.** This package is prepared for signature. No one has signed on anyone's behalf;
every signature line below is blank until the named person signs.

## 1. What is handed over

| # | Item | Location | Receiver |
|---|---|---|---|
| 1 | Executive summary with the Day 1 vs Day 9 matrix and Phase 3 backlog | [dept3-phase2-executive-summary.md](dept3-phase2-executive-summary.md) | Department 3 lead |
| 2 | Live demo checklist and verified transcript (23/23) | [dept3-live-demo-checklist.md](dept3-live-demo-checklist.md), [dept3-live-demo-transcript.md](dept3-live-demo-transcript.md), `scripts/live_demo.py` | All stakeholders |
| 3 | Frozen production configuration, verification script and test | [dept3-production-config-freeze-spec.md](dept3-production-config-freeze-spec.md), `config/production_freeze_v1.json`, `config/production.env.example`, `scripts/freeze_config.py`, `tests/test_config_freeze.py` | Platform |
| 4 | Operations runbook (deploy, knowledge update, index rebuild, alerts, rollback, incidents) | [dept3-operations-runbook.md](dept3-operations-runbook.md), [dept3-monitoring-runbook.md](dept3-monitoring-runbook.md) | Platform, QA |
| 5 | Approved knowledge base (363 chunks, 23 sources), standardized set, ingestion pipeline and reports | `data/kb/`, `scripts/ingest_dept3.py`, [dept3-ingestion-master-checklist.md](dept3-ingestion-master-checklist.md) | Content owner |
| 6 | Grounded answer, conversation and safety rulebooks | [dept3-grounded-rulebook.md](dept3-grounded-rulebook.md), [dept3-conversation-ux-rulebook.md](dept3-conversation-ux-rulebook.md), [safety-guardrails.md](safety-guardrails.md) | QA, dialogue |
| 7 | Evaluation assets: judged questions, attack suite v1.1, 18 adversarial cases, 8 journeys, regression runner | `data/retrieval_eval/`, `data/safety_eval/`, `scripts/e2e_regression.py`, `scripts/conversation_ux_eval.py` | QA |
| 8 | Reports: regression, before/after matrix, defect triage (43 entries), defect closure | [dept3-e2e-regression-report.md](dept3-e2e-regression-report.md), [dept3-before-after-matrix.md](dept3-before-after-matrix.md), [dept3-final-defect-triage-log.md](dept3-final-defect-triage-log.md), [dept3-final-defect-closure-report.md](dept3-final-defect-closure-report.md) | All |

## 2. Acceptance criteria

| # | Criterion | Target | Result | Evidence | Met |
|---|---|---|---|---|---|
| A1 | Release acceptance, critical / major | 25/25 · 6/6 | 25/25 · 6/6 | `data/dept3_e2e/release_gate_*` | yes |
| A2 | Safety suite v1.1, 4 configurations | cleared | cleared ×4 | `data/safety_eval/clearance/` | yes |
| A3 | No regression on previously passing cases | 0 | 0 (16 of 16, 19-question Day 1 set, 139-question release set) | e2e regression report | yes |
| A4 | Day 1 failed questions | ≥ 17 of 19 | 17 | before/after matrix | yes |
| A5 | Citation precision, 159 judged questions | ≥ 0.86 | 0.931 | `data/dept3_e2e/e2e_results.json` | yes |
| A6 | Multi-turn journeys / adversarial cases | all | 8/8 · 18/18 | `data/dept3_conversation/` | yes |
| A7 | Knowledge latency p95 / account p95 | < 250 · < 150 ms | 34 · 11 ms | scorecard | yes |
| A8 | Figures only for the requester | 0 violations | 0 (22 isolation tests) | test suite | yes |
| A9 | Frozen configuration verifies | pass | `FREEZE OK` | `freeze_config.py --verify` | yes |
| A10 | Live demonstration | all steps | 23 of 23 | demo transcript | yes |
| A11 | Tests | all pass | 840 pass; 1 stale test in the XICTEK module (expects no search index, the repository ships one) | pytest | **with condition C5** |
| A12 | Real account figures | real backend | mock backend | D3-01 | **not met; condition C1** |

## 3. Conditions of acceptance

| # | Condition | Owner | Due |
|---|---|---|---|
| C1 | Account figures are demo data until the authenticated backend is connected (D3-01). Not exposed to real users before then | Hassan Hussain | before any production launch |
| C2 | Knowledge base refreshed from the live site with the content owner (E2E-07); the 27 Oct snapshot is what the freeze contains | Fahad Zubairi + Mian Usman Khalid | first 30-day cycle |
| C3 | A real model provider is enabled only after passing the runbook section 2.1 gate and a wording review (D3-16) | Muhammad Hamza Nawaz | when a provider is chosen |
| C4 | Release tag `dept3-freeze-v1.0` created on the signed commit | Release owner | at sign-off |
| C5 | The stale XICTEK test updated to use a temporary index folder | XICTEK owner | next sprint |
| C6 | Production settings applied from `config/production.env.example` (notably `GROUNDED_ANSWERS_ENABLED=true`), secrets from the secret store | Platform | at deployment |

## 4. Open items handed over

18 open or partial entries in [the triage log](dept3-final-defect-triage-log.md) (P0 1, P1 9, P2 5, P3 3) and 3
accepted with reasons; the Phase 3 backlog with owners is section 7 of the executive summary. The first three are:
connect the backend, publish the missing help pages, refresh the knowledge base from the live site.

## 5. Knowledge transfer

| Topic | Material | Session |
|---|---|---|
| Operating the service (deploy, alerts, rollback) | runbook sections 2, 5, 6 | Platform on call |
| Knowledge base update and index rebuild | runbook sections 3 and 4; ingestion checklist | Content owner and platform |
| Adding a test case or changing a rule | rulebooks; freeze spec section 6; regression runner | QA and dialogue |
| Reading the logs and metrics | monitoring runbook | Platform, QA |

Sessions to be scheduled by the Department 3 lead: date ____________.

## 6. Sign-off

By signing, the receiver confirms they have received the items in section 1, reviewed the live demonstration result,
and accept the handover **with the conditions in section 3** (strike any condition not accepted and note it).

| Role | Name | Accepts | Signature | Date |
|---|---|---|---|---|
| Department 3 lead (approver) | ______________ | ☐ accept ☐ accept with conditions ☐ reject | ______________ | ________ |
| Core services (backend, C1) | Hassan Hussain | ☐ ☐ ☐ | ______________ | ________ |
| Dialogue and intents | Saba Talat | ☐ ☐ ☐ | ______________ | ________ |
| Content owner (knowledge base, C2) | Mian Usman Khalid | ☐ ☐ ☐ | ______________ | ________ |
| QA and red-team | Syeda Isma Nazir | ☐ ☐ ☐ | ______________ | ________ |
| LLM provider (C3) | Muhammad Hamza Nawaz | ☐ ☐ ☐ | ______________ | ________ |
| Platform operations (C4, C6) | ______________ | ☐ ☐ ☐ | ______________ | ________ |

**Handed over by:** Fahad Zubairi, AI intern · Signature: ______________ · Date: ________

Comments from receivers: _______________________________________________________________
