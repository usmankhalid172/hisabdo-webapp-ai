# Department 3 Phase 2 Final Executive Summary Report

Report date: 18 November 2026
Project: HisabDo Expense Management Chatbot
Department: 3
Phase: 2

## 1. Executive Summary

Phase 2 work improved retrieval evaluation, response grounding, citation handling, regression coverage, and operational documentation. The repository contains a frozen proof of concept configuration and maintenance runbooks.

Local automated tests passed. Offline retrieval experiments show that feature_intent_020 achieved the strongest reported ranking results. However, this experimental strategy is not verified as part of the active API runtime.

The live production demonstration and stakeholder walkthrough have not been verified in this evidence package. Production backend integration, production provider validation, and formal stakeholder approval remain pending.

Overall status: TECHNICAL DOCUMENTATION READY, PRODUCTION HANDOVER PENDING.

## 2. Day 1 Reference and Current Benchmark

The Day 1 reference dataset contains 71 cases, with 55 answerable cases and 16 no answer or clarification cases.

The current offline benchmark contains 71 cases, with 60 answerable source cases and 11 no source cases.

| Metric | Day 1 reference | Current offline TF IDF |
|---|---:|---:|
| Total cases | 71 | 71 |
| Answerable cases | 55 | 60 |
| No answer or no source cases | 16 | 11 |
| Hit at 1 | 89.09% | 88.33% |
| Hit at 3 | 96.36% | 95.00% |
| Hit at 5 | Not recorded | 96.67% |

The datasets have different answerable case counts and classifications. The figures are not a controlled before and after comparison. The current TF IDF results must not be described as a confirmed regression or improvement over Day 1.

## 3. Current Offline Strategy Results

The current benchmark evaluates 60 answerable source cases across 12 corpus documents.

| Strategy | Hit at 1 | Hit at 3 | Hit at 5 |
|---|---:|---:|---:|
| TF IDF baseline | 88.33% | 95.00% | 96.67% |
| Normalized TF IDF | 88.33% | 95.00% | 96.67% |
| BM25 | 85.00% | 96.67% | 98.33% |
| BM25 and TF IDF hybrid | 93.33% | 96.67% | 98.33% |
| Expanded hybrid | 91.67% | 96.67% | 100.00% |
| Expanded hybrid reranked | 90.00% | 95.00% | 98.33% |
| Metadata filtered hybrid | 81.67% | 91.67% | 93.33% |
| Feature intent reranked | 93.33% | 98.33% | 100.00% |
| Feature intent 015 | 93.33% | 98.33% | 100.00% |
| Feature intent 020 | 95.00% | 98.33% | 100.00% |
| Feature intent 025 | 95.00% | 98.33% | 100.00% |

The strongest reported offline result is shared by feature_intent_020 and feature_intent_025.

Compared with the current offline TF IDF baseline on the same 60 answerable cases, feature_intent_020 records:
1. Hit at 1 improvement of 6.67 percentage points.
2. Hit at 3 improvement of 3.33 percentage points.
3. Hit at 5 improvement of 3.33 percentage points.

These results are offline benchmark measurements. They do not establish that the experimental strategy is active in the chatbot API.

Benchmark limitations:
1. No dense embedding model was installed or measured.
2. BM25 is a local implementation, not rank_bm25.
3. Hybrid scores combine normalized BM25 and TF IDF scores with equal weights.
4. Metadata filtering is a heuristic experimental product area filter.
5. Reranking uses lexical overlap, not a learned cross encoder.

## 4. Active POC Runtime Configuration

The frozen POC runtime uses the following documented settings:

| Setting | Frozen POC behavior |
|---|---|
| Retrieval method | TF IDF |
| Similarity | Cosine similarity |
| Vectorizer | TF IDF with English stop words |
| Relevance threshold | 0.30 |
| Service retrieval count | Top 3 |
| Dense embeddings | Not installed or measured |
| Experimental hybrid strategies | Not verified in active API |

The experimental BM25, hybrid, feature intent and reranking strategies must not be represented as active production settings without implementation and runtime verification.

The prompt policy requires grounded responses, avoids unsupported product claims and source links, asks for clarification when needed, and supports safe abstention when evidence is missing.

Personal financial values must come from the authenticated backend API. They must not be obtained from FAQ retrieval.

Configuration defaults documented in the repository include development mode and a mock LLM provider. Production secrets and provider settings require secure environment configuration. No secret values belong in this report.

## 5. Quality, API and Test Evidence

The 16 November benchmark matrix recorded:
1. Local automated suite: 341 passed, 4 skipped, 1 warning at that checkpoint.
2. Local mean latency: 8.79 ms.
3. Local median latency: 8.11 ms.
4. Local P95 latency: 14.20 ms.
5. Five local FAQ API smoke tests: five successful HTTP responses, four correct RAG routes, four responses with citations, and zero responses with source URLs.

The smoke test exposed an export question routing issue and incomplete citation attribution. Subsequent defect closure work on 17 November documented fixes for procedural export routing and citation completeness. Approved source URLs remain an open issue.

The latest recorded full local test run on 17 November was 346 passed, 4 skipped, and 1 warning in 10.53 seconds.

These are local test results. They do not establish production backend behavior, production provider behavior, or production network latency.

## 6. Improvements Documented During Phase 2

1. Retrieval evaluation expanded to 71 cases.
2. Multiple offline retrieval strategies were benchmarked.
3. Grounded response and citation rules were reviewed.
4. Procedural export routing regression was addressed.
5. Citation completeness regression was addressed.
6. Prompt injection pattern duplication was removed.
7. Production configuration and operational maintenance documentation were prepared.
8. Security, privacy and cross user regression tests were maintained.

The improvements above are supported by repository documentation and local test evidence. Live production behavior still requires demonstration.

## 7. Open Production Blockers

| ID | Blocker | Required evidence |
|---|---|---|
| P0 | Approved real financial backend data contract | Approved contract and integration evidence |
| P0 | Production backend configuration | Secure configuration and successful production integration tests |
| P0 | Customer ownership and session isolation | Authenticated ownership tests, including concurrent sessions |
| P1 | Generated answer quality scoring | Reviewed answer rubric results for correctness, citations, completeness, language and abstention |
| P1 | Final security review | Security reviewer approval and recorded findings |
| P1 | Canonical RAG and LLM execution path | Architecture decision and runtime verification |
| P1 | Approved payable, Khata and Udhar instructions | Product approved source material |
| P2 | Official source URLs and content ownership | Approved URLs, named content owners and review dates |
| P2 | Production latency and provider cost | Production p50, p95, p99 and usage evidence |
| P2 | Retrieval refresh monitoring | Failure logs, alerts and recovery evidence |

## 8. Phase 3 Recommendations

1. Reconcile and freeze one canonical evaluation dataset with consistent answerable and no answer labels.
2. Run the Day 1 reference and current retrieval methods against the same dataset and settings.
3. Integrate and evaluate the selected experimental retrieval strategy in the actual API before considering adoption.
4. Add a reviewed generated answer quality rubric covering factual correctness, citation correctness, completeness, language and safe abstention.
5. Complete authenticated backend integration and cross customer isolation tests.
6. Obtain approved product instructions and official source URLs for payable, Khata, Udhar, reminders and support.
7. Add production monitoring for retrieval failures, response latency, provider usage and cost.
8. Run a controlled production demonstration using authorized test accounts and approved synthetic or test data.
9. Obtain formal sign off from the Project Lead, Backend API Owner, QA Owner, Security Reviewer and Product Owner.

## 9. Live Demonstration Status

Status: NOT VERIFIED IN THIS REPORT.

No production session evidence, stakeholder attendance record, or signed demonstration result was supplied for this report.

The separate Live Demo Verification Checklist defines the required walkthrough and evidence to collect. A local test run or offline benchmark is not a substitute for a live production demonstration.

## 10. Formal Handover Status

Status: PENDING.

The documentation package can be reviewed, but production handover approval requires:
1. Resolution or explicit acceptance of all P0 blockers.
2. Approved production configuration.
3. Verified live demonstration evidence.
4. QA and security review results.
5. Named accountable owners and agreed follow up dates.
6. Signatures from authorized stakeholders.

The Formal Handover Sign Off Package provides the approval fields. No stakeholder approval or signature is assumed.

## 11. Source Documents

The report consolidates evidence from:
1. docs/department3_baseline_comparison_final.md
2. docs/department3_before_after_quality_latency_benchmark_matrix.md
3. docs/department3_retrieval_benchmark_results.json
4. docs/department3_production_configuration_freeze_spec.md
5. docs/department3_operational_maintenance_deployment_runbook.md
6. docs/department3_phase2_day1_ownership_matrix.md
7. docs/department3_phase2_day1_prioritized_issues.md
8. docs/department3_final_evaluation_scorecard.md
9. docs/department3_final_defect_closure_report.md

## 12. Final Conclusion

Department 3 Phase 2 has documented retrieval experiments, grounded response controls, regression fixes, a frozen POC configuration and operational guidance. The current offline benchmark identifies feature_intent_020 as the strongest reported strategy, but it is not verified as active in the API.

Local automated tests passed at the latest recorded checkpoint. Production readiness is not established because live backend integration, complete answer quality evaluation, approved content sources, production measurements, live demonstration and stakeholder sign off remain pending.

Final recommendation: retain the current frozen POC configuration, complete the listed production blockers, and defer formal production handover until the required evidence and approvals are recorded.
