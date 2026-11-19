# Department 3 Phase 2 Formal Handover Sign Off Package

Project: HisabDo Expense Management Chatbot
Department: 3
Phase: 2
Package date: 18 November 2026

## 1. Handover Purpose

This package records the technical documentation prepared for Department 3 Phase 2 and defines the evidence and approvals required for formal handover.

It consolidates:
1. Department 3 Phase 2 Final Executive Summary Report.
2. Live Demo Verification Checklist.
3. Frozen production configuration specification.
4. Operational maintenance and deployment runbook.
5. Retrieval benchmark results and baseline comparison.
6. Final evaluation and defect closure evidence.
7. Open production blockers and Phase 3 recommendations.

Current handover status: PENDING APPROVAL.

## 2. Handover Package Contents

| Deliverable | File | Status |
|---|---|---|
| Executive summary | docs/department3_phase2_final_executive_summary_report.md | Prepared |
| Live demo checklist | docs/department3_live_demo_verification_checklist.md | Prepared, execution pending |
| Formal handover package | docs/department3_formal_handover_signoff_package.md | Prepared |
| POC configuration freeze | docs/department3_production_configuration_freeze_spec.md | Existing reference |
| Operational maintenance runbook | docs/department3_operational_maintenance_deployment_runbook.md | Existing reference |
| Retrieval benchmark | docs/department3_retrieval_benchmark_results.json | Existing evidence |
| Baseline comparison | docs/department3_baseline_comparison_final.md | Existing evidence |
| Quality and latency matrix | docs/department3_before_after_quality_latency_benchmark_matrix.md | Existing evidence |
| Final evaluation scorecard | docs/department3_final_evaluation_scorecard.md | Existing reference |
| Defect closure report | docs/department3_final_defect_closure_report.md | Existing reference |

## 3. Technical Handover Summary

### Retrieval

The active POC API retriever is documented as TF IDF with cosine similarity, relevance threshold 0.30 and top 3 results.

The offline benchmark tested local BM25, equal weight normalized BM25 and TF IDF hybrid, expansion, heuristic metadata filtering and lexical overlap reranking.

The strongest reported offline result is feature_intent_020:
1. Hit at 1: 95.00%.
2. Hit at 3: 98.33%.
3. Hit at 5: 100.00%.

This result is not evidence of active API integration. Dense embeddings were not measured.

### Grounded answers and citations

The prompt policy requires answers to be based on available evidence, avoids unsupported product claims and supports clarification or safe abstention when sources are missing.

Procedural export routing and citation completeness defects were addressed in the documented regression work. Approved source URLs remain outstanding.

### Personal financial data

Personal financial values must be obtained from the authenticated backend API, not FAQ retrieval.

The real production backend data contract, production integration and complete customer session isolation evidence remain required before production acceptance.

### Automated validation

The latest recorded full local test run on 17 November 2026 was:
346 passed, 4 skipped, 1 warning, 10.53 seconds.

This is local automated test evidence, not production verification.

## 4. Frozen POC Configuration and Change Control

The current POC configuration must remain the reference configuration until an authorized technical owner approves a change.

| Configuration area | Documented POC setting |
|---|---|
| Retrieval | TF IDF |
| Similarity | Cosine similarity |
| Vectorizer | English stop words |
| Relevance threshold | 0.30 |
| Retrieval count | Top 3 |
| Dense embedding model | Not installed or measured |
| Experimental strategies | Not verified in active API |

Production configuration approval is separate from the POC freeze.

No production secrets, tokens, credentials or private configuration values should be copied into this package.

Any proposed retrieval or prompt change must include:
1. Change description and reason.
2. Impact on retrieval and response behavior.
3. Relevant automated regression results.
4. Security and privacy review where applicable.
5. Approval by the designated technical owner.
6. Updated configuration and maintenance documentation.

## 5. Operational Ownership

The Day 1 ownership matrix defines accountable roles. Individual names and deadlines still require Project Lead confirmation.

| Work area | Accountable role |
|---|---|
| Architecture and priority decisions | Project Lead / Technical Lead |
| Retrieval, RAG and prompt integration | Department 3 AI/ML Intern |
| Authenticated financial backend | Backend API Owner |
| Approved product knowledge and source URLs | Knowledge Base / Product Content Owner |
| Evaluation and regression evidence | QA / Evaluation Owner |
| Privacy and security approval | Security Reviewer |
| Product feature confirmation | Product Owner |

The Project Lead must enter the actual assigned individual names and dates before accepting the handover.

## 6. Open Blockers and Required Owners

| ID | Open item | Priority | Accountable role | Acceptance evidence |
|---|---|---|---|---|
| H01 | Approve real financial backend data contract | P0 | Backend API Owner | Approved contract |
| H02 | Configure and verify production backend | P0 | Backend API Owner | Production integration tests |
| H03 | Verify customer ownership and session isolation | P0 | Security Reviewer | Ownership and concurrent session tests |
| H04 | Complete generated answer quality evaluation | P1 | QA / Evaluation Owner | Scored golden set |
| H05 | Complete final security review | P1 | Security Reviewer | Signed review |
| H06 | Confirm canonical RAG and LLM execution path | P1 | Project Lead | Architecture decision |
| H07 | Obtain approved payable, Khata and Udhar sources | P1 | Knowledge Base Owner | Approved instructions |
| H08 | Verify official support details and reminder claims | P1 | Product Owner | Product approval |
| H09 | Add official source URLs and ownership metadata | P2 | Knowledge Base Owner | Verified source records |
| H10 | Measure production latency and provider usage | P2 | Backend API Owner | Production metrics |
| H11 | Complete live production demonstration | P0 | Project Lead and QA Owner | Completed checklist and evidence |
| H12 | Obtain stakeholder acceptance | P0 | Project Lead | Recorded approvals |

## 7. Handover Acceptance Conditions

Formal handover can be accepted only after the following conditions are met:

1. All P0 blockers are resolved and verified.
2. Production backend and authentication behavior are tested.
3. Customer ownership and session isolation pass.
4. The live demo checklist is completed with actual evidence.
5. Retrieval, grounded answers, citations and safe abstention are reviewed.
6. Security review is complete.
7. Production configuration and runbook are approved.
8. Open P1 and P2 issues have named owners and agreed due dates.
9. Stakeholders review and sign the handover decision.

A local test pass or prepared document alone does not satisfy production acceptance.

## 8. Outstanding Phase 3 Work

1. Freeze one reconciled evaluation dataset and compare strategies using identical cases.
2. Verify the selected experimental retrieval strategy in the active API before adoption.
3. Add generated answer scoring for correctness, citations, completeness and language.
4. Complete real backend integration and concurrent customer isolation tests.
5. Obtain approved product content and official source URLs.
6. Add production monitoring for retrieval, errors, latency and provider costs.
7. Improve refresh failure alerts and recovery procedures.
8. Repeat the full live demonstration after blockers are closed.

## 9. Formal Handover Decision

Not applicable.

Decision options:
1. ACCEPTED: All mandatory conditions satisfied and evidence reviewed.
2. ACCEPTED WITH ACTIONS: Only permitted non blocking actions remain, with owners and due dates recorded.
3. REJECTED: Mandatory evidence or controls are incomplete.
4. DEFERRED: Formal decision postponed until required evidence is available.

Current decision: DEFERRED, PENDING LIVE DEMONSTRATION AND APPROVAL.

Reason:
Production backend verification, live demonstration evidence, final security review and stakeholder approvals have not been supplied in this package.

## 10. Stakeholder Sign Off

### Project Lead / Technical Lead

Name: __________________________________

Decision: _______________________________

Comments: ______________________________

Signature: ______________________________

Date: __________________________________

### Backend API Owner

Name: __________________________________

Decision: _______________________________

Comments: ______________________________

Signature: ______________________________

Date: __________________________________

### QA / Evaluation Owner

Name: __________________________________

Decision: _______________________________

Comments: ______________________________

Signature: ______________________________

Date: __________________________________

### Security Reviewer

Name: __________________________________

Decision: _______________________________

Comments: ______________________________

Signature: ______________________________

Date: __________________________________

### Product Owner

Name: __________________________________

Decision: _______________________________

Comments: ______________________________

Signature: ______________________________

Date: __________________________________

## 11. Handover Record

| Field | Value |
|---|---|
| Package prepared | 18 November 2026 |
| Technical documentation | Prepared |
| Local automated test evidence | Recorded |
| Offline benchmark evidence | Recorded |
| Production demonstration | Pending |
| Production backend acceptance | Pending |
| Security approval | Pending |
| Stakeholder signatures | Pending |
| Final handover decision | Deferred |

## 12. Final Declaration

This document records the available Phase 2 technical evidence and the remaining acceptance requirements. It does not claim that production deployment, live stakeholder demonstration or formal handover approval has occurred.

The handover becomes effective only when authorized stakeholders review the evidence, resolve mandatory blockers and record their decisions and signatures.

Final status: HANDOVER PACKAGE PREPARED, FORMAL SIGN OFF PENDING.
