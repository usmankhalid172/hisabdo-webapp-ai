# Department 3 — Phase 2 Final Executive Summary Report

**Project:** HisabDo Expense Management Chatbot  
**Department:** Department 3  
**Report Date:** 18 November 2026  
**Status:** Documentation prepared; production demonstration and formal handover pending.

## 1. Executive Summary

Phase 2 focused on improving the HisabDo expense management chatbot through retrieval evaluation, grounded responses, citation handling, multi-turn financial flows, security guardrails, and operational readiness.

Existing project documentation records defect remediation, regression testing, retrieval benchmarks, a local configuration specification, and an operational maintenance runbook.

However, production deployment and production-level validation have not been established by the available evidence. This report therefore distinguishes documented local results from production outcomes that still require verification.

## 2. Day 1 Baseline and Later Evaluation Evidence

### Day 1 baseline

The available historical retrieval evaluation records:
- 41 verified questions in the evaluation set.
- 30 expected-source matches.
- 11 misses.
- Source-match rate: 73.17%.

The earlier recorded full test run reported:
- 408 passed.
- 4 skipped.
- 0 failed.
- 2 warnings.

### Later recorded evaluation evidence

The defect closure documentation prepared on 17 November 2026 records:
- 456 passed.
- 4 skipped.
- 0 failed.
- 2 dependency warnings.
- Test duration: 74.92 seconds.
- A separate focused regression run: 31 passed, 0 failed, 2 warnings.

Separately recorded historical retrieval benchmark results (not established as Day 9 results):
- Dense top-3: 95.12%.
- BM25: 92.68%.
- Hybrid RRF: 95.12%.
- Hybrid Metadata: 82.93%.
- Hybrid Metadata + Rerank: 85.37%.
- Dense MRR: 0.913.

**Important:** These are recorded evaluation results, not proof of live production performance. The available evidence does not yet establish a complete, directly comparable Day 1 versus Day 9 benchmark across all requested dimensions. That comparison remains pending source verification.

## 3. Benchmark Evidence Limitations

The Day 1 audit establishes a verified-source match rate of 73.17% (30/41). The available records do not establish a comparable Day 9 chatbot retrieval or answer-quality result. The separately recorded 95.12% Dense top-3 result and other retriever results must not be presented as Day 9 improvements without matching run dates and evaluation evidence.

The 78.64% accuracy and 79.03% weighted F1-score in Tasks 27 and 28 belong to the separate Smart Expense Categorization classifier, not the chatbot retrieval or answer-generation evaluation. They are not evidence of Day 1-to-Day 9 chatbot improvement.

The reviewed test records also report different runs: 408 passed in the Day 1 audit, 351 passed in the separate evaluation report, and 456 passed in the later defect closure report. These are separate recorded runs and must not be treated as a directly comparable trend without run-level traceability.

## 4. Retrieval, Grounding and Citation Improvements

The documented implementation includes:
- Verified knowledge filtering (`verified is True`).
- Retrieval relevance threshold of 0.40.
- Top-k retrieval setting of 3.
- Context limit of 5 chunks and 3,000 characters.
- Citation metadata forwarding in the FAQ context helper.
- Regression coverage for FAQ citation metadata.
- Abstention when sufficient verified evidence is unavailable.

Fresh production citation accuracy and independent answer-level grounding evaluation remain pending.

## 5. Frozen Configuration — Current Documented Local Baseline

| Component | Documented setting |
|---|---|
| Main retrieval module | `src/financial_assistant/faq_rag.py` |
| Vector store | LangChain InMemoryVectorStore |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Execution device | HuggingFace CPU |
| Similarity threshold | 0.40 |
| Retrieval top-k | 3; maximum 10 |
| Knowledge filtering | Verified documents only |
| Knowledge base version | 1.0.0 |
| Context chunks | Maximum 5 |
| Context length | Maximum 3,000 characters |
| Default LLM | `gpt-4o-mini` |
| LLM timeout | 15 seconds |
| Maximum retries | 1 |
| Maximum input length | 1,000 characters |
| API key environment variable | `FINANCIAL_ASSISTANT_LLM_API_KEY` |

This is a documented local baseline, not an approved production freeze. Model revision pinning, production secrets, real backend integration, trusted identity, and production retrieval settings still require approval and verification.

## 6. Safety and Financial Data Protection

Documented safeguards include:
- Prompt-injection and unsafe-history checks.
- Out-of-scope and malformed-input handling.
- Sensitive-output restrictions.
- Third-party financial information refusal.
- Verified-source-only answer grounding.
- Safe fallback when backend services are unavailable.
- Authenticated user identity checks in the API layer.

Production cross-user isolation and privacy testing against a real backend remain release blockers.

## 7. Multi-Turn Financial Flows

The project documentation records financial conversation handling and safe transaction guidance. However, independent production verification of transaction, budget, multi-period comparison, and trends/aggregate flows is not complete. Four data-dependent use cases were recorded as skipped.

No claim of successful production transaction execution or financial data persistence is made in this report.

## 8. Operational Readiness

An operational maintenance and deployment runbook is available at:

`docs/operations/operational_maintenance_deployment_runbook.md`

It documents knowledge-base update procedures, index rebuild and validation, monitoring, rollback, and deployment prerequisites.

Production deployment remains conditional on:
- Real financial backend integration.
- Trusted authenticated identity.
- Cross-user isolation tests.
- Production secret configuration.
- Monitoring and rollback ownership.
- Completion of skipped financial use cases and production acceptance tests.

## 9. Open Backlog and Phase 3 Recommendations

1. Integrate and validate the real financial backend.
2. Replace development placeholder credentials with managed production secrets.
3. Establish trusted identity propagation and production cross-user isolation.
4. Complete the four skipped financial use cases.
5. Run independent multi-turn financial-flow tests.
6. Measure answer-level grounding and citation accuracy.
7. Compare Day 1 and Day 9 using the same evaluation dataset and metrics.
8. Evaluate retrieval quality after any approved production configuration change.
9. Establish production latency, monitoring, alerting, and rollback thresholds from measured data.
10. Assign knowledge-base ownership, review schedules, and approval responsibilities.

## 10. Live Demonstration and Stakeholder Walkthrough

**Status: Pending actual execution.**

The following must be demonstrated in the live environment and supported by recorded evidence:
- Retrieval accuracy against the approved evaluation questions.
- Grounded answers with supporting inline citations.
- Multi-turn financial conversations.
- Safe handling of unavailable or unverified information.
- Authentication and user-data isolation.
- Guardrail behavior under unsafe or out-of-scope inputs.

The demonstration date, environment, attendees, test outcomes, and stakeholder feedback must be recorded after the walkthrough. No live demonstration is claimed as completed in this report.

## 11. Final Handover Status

**Overall disposition: PARTIALLY COMPLETE — NOT PRODUCTION CLEARED.**

The available documentation and local evaluation evidence are prepared for review. Production demonstration, stakeholder acceptance, and formal sign-off remain pending.

Formal handover can be completed only after the authorized stakeholder reviews the evidence and records an approval decision.

---
**Prepared for:** Department 3 — HisabDo Phase 2  
**Prepared on:** 18 November 2026  
**Document status:** Draft for evidence review and stakeholder walkthrough



## Focused Final Verification — 19 November 2026

The focused Department 3 verification run covered 11 test files across chatbot behavior, FAQ retrieval, retrieval security, guardrails, API authentication, multilingual handling, use cases, ingestion, monitoring, and synthetic/user isolation.

Result: 142 passed, 4 skipped, 0 failed, 2 deprecation warnings, completed in 33.14 seconds.

The four skipped tests require a financial data retrieval layer for transaction-level answers, budget answers, multi-period comparisons, and trend/aggregate insights. These use cases remain blocked and are not considered production-verified.

Conversational history and FAQ follow-up tests are included in the local test coverage. This does not establish successful end-to-end production financial workflows.

Production demonstration, stakeholder walkthrough, and formal approval remain pending.
