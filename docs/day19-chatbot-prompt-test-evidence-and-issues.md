\# Day 19 — Chatbot Prompt/Test Evidence, Consolidated Issues \& Roadmap to Day 30



\*\*Project:\*\* HisabDo Web App AI  

\*\*Department:\*\* Department 1 – Capstone Development  

\*\*Track:\*\* AI/ML  

\*\*Workstream:\*\* AI Financial Assistant / Chatbot  

\*\*Intern:\*\* Rameesha Zafar  

\*\*Task:\*\* Consolidate chatbot prompt/test-case evidence, document unresolved response issues, and define next testing priorities toward Day 30  

\*\*Day:\*\* 19  



\---



\## 1. Objective



The objective of Day 19 is to synthesize all research, prompt engineering specifications, query scenario matrices, and integration test plans developed from Day 15 to Day 18 into a unified evidence and roadmap document.



This document serves to:

\* Provide a consolidated summary of prompt and test-case coverage across the AI Financial Assistant workstream.

\* Reference existing GitHub evidence, pull requests, and documentation artifacts.

\* Categorize and detail all unresolved response issues, execution blockers, and missing backend/AI dependencies.

\* Clearly audit test statuses (`PASS`, `FAIL`, `BLOCKED`, `NOT TESTED`) following strict project accuracy rules.

\* Define a strategic, phased testing roadmap to guide workstream execution through Day 30.



\---



\## 2. Prompt \& Test Case Coverage Summary



Across Days 15–18, a total of 25 comprehensive test cases and 24 end-to-end integration query scenarios were designed to evaluate the AI Financial Assistant's behavior.



\### Coverage Breakdown

\* \*\*Expense Summaries \& Periods:\*\* Daily, weekly, monthly, and custom date range queries (`TC-01`, `TC-02`, `TC-12`, `INT-01`, `INT-06`).

\* \*\*Category Analytics:\*\* Category-filtered spending and top-spending category identification (`TC-03`, `TC-04`, `INT-02`, `INT-03`).

\* \*\*Transaction Records:\*\* Recent expense fetching and maximum transaction identification (`TC-05`, `TC-06`, `INT-04`, `INT-05`).

\* \*\*Budget Tracking \& Math:\*\* Remaining budget, usage percentage, over-budget alerts, and missing budget handling (`TC-07` to `TC-09`, `TC-15`, `INT-07` to `INT-10`).

\* \*\*Comparative Analytics:\*\* Month-over-month comparisons and category shift tracking (`TC-10`, `TC-11`, `INT-11`, `INT-12`).

\* \*\*Ambiguity \& Context Memory:\*\* Clarification handling, missing parameters, multi-intent queries, and multi-turn context retention (`TC-13`, `TC-14`, `TC-21`, `TC-22`, `INT-13`, `INT-14`, `INT-17`, `INT-18`).

\* \*\*Safety, Guardrails \& Out-of-Scope:\*\* Jailbreak resistance, sensitive personal data protection, non-financial prompt redirection, and zero-spending edge cases (`TC-17` to `TC-20`, `TC-24`, `INT-19` to `INT-22`).



\---



\## 3. Evidence \& Repository Artifact Audit



All workstream deliverables have been systematically documented and pushed to the project repository (`https://github.com/usmankhalid172/hisabdo-webapp-ai`):



| Day | Task Focus | Branch Name | Key Documentation File | Status |

| :--- | :--- | :--- | :--- | :--- |

| \*\*Day 15\*\* | Prompts \& Test Specification | `feature/rameesha-financial-assistant-prompts` | `docs/day15-financial-assistant-prompts-and-test-cases.md` | Submitted (PR #4) |

| \*\*Day 16\*\* | Initial Test Execution Checks | `feature/rameesha-zafar-chatbot-testing-day-16` | `docs/day16-chatbot-test-queries-and-response-checks.md` | Submitted |

| \*\*Day 17\*\* | Financial Query Scenarios | `feature/rameesha-zafar-financial-query-scenarios-day-17` | `docs/day17-financial-query-scenarios-and-validation.md` | Submitted |

| \*\*Day 18\*\* | Integration Test Scenarios | `feature/rameesha-zafar-chatbot-integration-tests-day-18` | `docs/day18-chatbot-integration-test-scenarios.md` | Submitted |

| \*\*Day 19\*\* | Evidence Synthesis \& Roadmap | `feature/rameesha-zafar-chatbot-test-evidence-day-19` | `docs/day19-chatbot-prompt-test-evidence-and-issues.md` | Current Deliverable |



\---



\## 4. Test Execution Status Audit



In compliance with project guidelines, no unexecuted tests have been marked as passed. Because live backend API routes and RAG pipelines remain under active development, the execution summary is as follows:



\* \*\*Total Test Cases Defined:\*\* 25  

\* \*\*Total Integration Scenarios Defined:\*\* 24  

\* \*\*Passed:\*\* 0  

\* \*\*Failed:\*\* 0  

\* \*\*Blocked / Not Tested:\*\* 49  



> \*\*Execution Note:\*\* Live verification is strictly \*\*BLOCKED\*\* pending the deployment of the chatbot query endpoint (`/api/v1/chatbot/query`) and database seed data.



\---



\## 5. Consolidated Unresolved Issues \& Missing Dependencies



| Issue ID | Domain | Description | Impacted Scope | Severity | Workstream Dependency | Target Resolution |

| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

| \*\*ISSUE-01\*\* | Backend API | Endpoint `/api/v1/chatbot/query` is not exposed or connected to the frontend/CLI execution interface. | All Test Cases \& Integration Scenarios | \*\*High\*\* | MERN Backend Team | Days 20–22 |

| \*\*ISSUE-02\*\* | Test Data | Lack of an automated database seed script providing 30 days of realistic mock user transactions and budget data. | Data-dependent queries (`TC-01`–`TC-12`, `INT-01`–`INT-12`) | \*\*High\*\* | Database / AI Team | Days 20–21 |

| \*\*ISSUE-03\*\* | Agent Architecture | Chat session memory buffer (`LangChain ConversationBufferMemory`) is unconfigured, breaking multi-turn context retention. | Multi-turn queries (`TC-22`, `INT-17`) | \*\*Medium\*\* | AI/ML Team | Days 23–24 |

| \*\*ISSUE-04\*\* | NLP / Parsing | Natural language date parsing engine for relative phrases ("weekend", "last month") is unintegrated. | Date queries (`TC-23`, `INT-06`, `INT-23`) | \*\*Medium\*\* | AI/ML Team | Days 23–25 |

| \*\*ISSUE-05\*\* | Guardrails | Secondary evaluation layer for verifying system prompt injection resistance under live LLM inference is unverified. | Safety queries (`TC-19`, `INT-21`) | \*\*Low\*\* | AI/ML Team | Days 26–27 |



\---



\## 6. Phased Testing Roadmap Toward Day 30



To transition the AI Financial Assistant from current specification artifacts to full production readiness by Day 30, the workstream will follow this phased testing roadmap:



\### Phase 1: Mock Data \& Local API Wiring (Days 20–22)

\* Collaborate with database leads to deploy JSON/MongoDB seed fixtures containing 30 days of standard transaction history.

\* Wire local Express/FastAPI server routes to accept test prompt payloads at `/api/v1/chatbot/query`.

\* Perform initial smoke testing on basic expense queries (`TC-01` to `TC-06`).



\### Phase 2: RAG Pipeline \& Multi-Turn Integration (Days 23–25)

\* Integrate LangChain vector retrieval / SQL agent with active transaction and budget database tables.

\* Configure conversational session memory (`sessionId`) to enable multi-turn context tracking (`INT-17`).

\* Validate natural language date parsing for relative timeframes (`INT-23`).



\### Phase 3: Automated Evaluation \& Guardrail Hardening (Days 26–28)

\* Convert manual test matrices into automated test scripts (e.g., PyTest or Jest testing suites).

\* Execute prompt-injection and jailbreak test suites (`TC-19`, `INT-21`) to verify LLM boundary enforcement under live inference.

\* Benchmark response latency, response conciseness, and data accuracy metrics.



\### Phase 4: Final Capstone Integration \& Documentation (Days 29–30)

\* Conduct complete end-to-end user testing via the frontend Web UI.

\* Consolidate final pass/fail metrics, execution logs, and performance reports.

\* Finalize workstream documentation for Capstone evaluation and handoff.

