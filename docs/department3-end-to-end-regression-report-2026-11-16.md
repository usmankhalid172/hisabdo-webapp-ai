# Department 3 End-to-End Regression Report

**Project:** HisabDo AI Business Assistant  
**Organization:** XICTEK Systems  
**Department:** Department 3  
**Prepared by:** Purnoor Zafar — AI/ML Intern  
**Report date:** 16 November 2026  
**Repository branch:** purnoor-zafar-ai-intern

## 1. Objective

Validate the integrated Phase 2 expense-management chatbot pipeline, including the cleaned knowledge base, tuned chunking, hybrid lexical-semantic retrieval, grounded prompting, source attribution rules, conversational UX, and safety/privacy guardrails.

The validation covered the available golden question set, retrieval benchmarks, security and adversarial tests, integration workflows, and the full automated test suite.

## 2. Scope and evidence

The following validation areas were executed:

- Golden FAQ retrieval evaluation using `tests/evaluation_question_set.json`.
- Hybrid retrieval evaluation and comparison with the TF-IDF baseline.
- Targeted chatbot, retrieval, hybrid retrieval, and grounded-generation tests.
- Security, privacy, cross-user boundary, and adversarial input tests.
- Integration workflow tests, including conversation-history forwarding.
- Full pytest suite.
- Retrieval precision, recall, and local retrieval latency benchmark.

## 3. Test execution results

| Validation area | Result | Outcome |
|---|---:|---|
| Targeted chatbot/retrieval/grounding tests | 28 passed, 1 warning | PASS |
| Security and adversarial tests | 70 passed, 1 warning | PASS |
| Integration workflow tests | 24 passed, 1 warning | PASS |
| Full test suite | 387 passed, 4 skipped, 69 warnings | PASS |
| Day 1 security baseline suite rerun | 62 passed, 1 warning | PASS |
| Golden retrieval top-1 | 10/10 | PASS |
| Unsupported/ambiguous no-match checks | 2/2 | PASS |

The full test suite completed with zero test failures. Skipped tests and warnings are recorded separately and should not be interpreted as failures.

## 4. Retrieval benchmark findings

The 10-question benchmark was executed twice, with 30 retrieval timing repetitions per question per run.

- Supported retrieval questions: 8.
- Top-1 expected-source accuracy: 8/8 (100%).
- Unsupported/ambiguous no-match checks: 2/2.
- Macro Precision@3: 0.4583 (45.83%).
- Macro Recall@3: 0.9583 (95.83%).
- EVAL-08 Recall@3: 0.6667; expected source `finance_001` was absent from the returned top three.
- Run 1 average retrieval latency: 1.405 ms.
- Run 2 average retrieval latency: 1.186 ms.
- Run 2 median retrieval latency: 1.345 ms.
- Run 2 minimum/maximum retrieval latency: 0.005 ms / 3.685 ms.
- Timing samples: 300 per run.

These latency figures measure local retrieval only. They exclude the LLM provider, API/network time, backend financial-data calls, and complete user-facing response generation.

## 5. Security and privacy validation

The Day 1 security suite was rerun and again produced 62 passing tests, matching the recorded Day 1 baseline of 62 passing tests.

The expanded security/adversarial suite produced 70 passing tests. Covered areas included prompt-injection attempts, secret-extraction probes, oversized and malformed inputs, adversarial retrieved content, third-party financial-data requests, and cross-user access boundaries.

These results demonstrate passing automated tests in the local test environment. They do not independently certify production deployment security or live account isolation.

## 6. Conversational and integration validation

The conversation-history forwarding test passed. The integration AI, Task 15–25 workflow, and workflow-client test groups also passed.

**Limitation:** The available test evidence confirms that conversation history is forwarded to the LLM provider. It does not independently prove a complete live multi-turn financial conversation, such as creating an expense and then asking follow-up questions about that transaction. This scenario remains to be validated.

## 7. Grounding and source attribution

Grounded-generation prompt rules were inspected and the targeted grounded-generation tests passed.

The documented rules require answers to rely on retrieved FAQ content, prohibit invented source IDs, titles, URLs, quotes, or citations, and direct personal financial queries through authorized backend routes.

**Limitation:** A dedicated end-to-end citation renderer and automatic source-conflict detection were not independently verified. Some knowledge-base records have null source URLs or pending source-verification metadata. Prompt rules alone do not prove that every generated response displays accurate inline citations.

## 8. Warnings and compatibility risks

The full suite reported 69 warnings, including:

- Persisted scikit-learn objects were created with scikit-learn 1.7.2, while the current environment uses 1.5.2. This is a model-persistence compatibility risk and should be resolved through a compatible runtime or controlled model rebuild.
- pytest-asyncio reported that the default fixture loop scope is not explicitly configured.
- Starlette/AnyIO reported a BlockingPortal deprecation warning.

These warnings did not cause test failures during this run.

## 9. Production verification limitations

The available evaluation documentation indicates that personal financial queries use a backend route and that demo financial figures may be returned by the current backend client. Live production financial data correctness and production session isolation were not verified as part of this local test run.

No end-to-end LLM/API response latency instrumentation was found in the inspected Python test files. Consequently, full chatbot response latency and provider usage costs are not reported.

## 10. Overall conclusion

The local automated regression evidence is positive: the full test suite passed with 387 passed and 4 skipped, the expanded security/adversarial tests passed 70/70, and the golden retrieval benchmark achieved 8/8 supported top-1 matches plus 2/2 no-match checks.

The system should be described as **locally regression-tested, with production and several end-to-end verification gaps still open**. The key follow-up items are the EVAL-08 missing top-three source, low Precision@3, production backend/session-isolation verification, full multi-turn financial-flow validation, end-to-end latency measurement, and citation-rendering verification.

No claim is made that these unverified production behaviors have been certified.
