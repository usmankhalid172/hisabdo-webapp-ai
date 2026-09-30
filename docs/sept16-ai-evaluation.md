\# Sept 16 AI Evaluation — Multi-Turn Conversation Benchmark



\## Objective



Evaluate the AI chatbot across consecutive multi-turn patient scenarios and measure:



\- Multi-turn request success rate

\- Conversation continuity

\- JSON response schema consistency

\- Response latency across consecutive calls



\## Test Environment



\- Endpoint: `POST /api/v1/chatbot`

\- Test client: FastAPI `TestClient`

\- LLM provider: `MockLLMProvider`

\- Test date: 2026-09-30

\- Test scenarios: 3

\- Turns per scenario: 3

\- Total multi-turn requests: 9



\## Test Scenarios



\### Scenario 1 — Headache Follow-Up



Three consecutive turns covering:



1\. Initial headache report

2\. Follow-up information request

3\. Additional mild fever symptom



\### Scenario 2 — Cough Follow-Up



Three consecutive turns covering:



1\. Initial cough report

2\. Follow-up information request

3\. Additional fatigue and mild fever



\### Scenario 3 — Chest Discomfort Follow-Up



Three consecutive turns covering:



1\. Initial chest discomfort report

2\. Follow-up information request

3\. Additional breathing difficulty



\## Results



| Metric | Result |

|---|---:|

| Total multi-turn requests | 9 |

| Successful requests | 9/9 |

| Success rate | 100% |

| JSON/schema-valid responses | 9/9 |

| Schema validity rate | 100% |

| Average latency | 8.78 ms |

| Minimum latency | 7.15 ms |

| Maximum latency | 14.72 ms |

| Test cases passed | 4/4 |



\## Validation Checks



The evaluation suite verified that:



\- Every request returned HTTP 200.

\- Every response matched the `ChatbotResponse` schema.

\- The expected `conversation\_id` was preserved across consecutive turns.

\- Response JSON keys remained consistent.

\- Conversation history was constructed and passed between consecutive requests.

\- Nine consecutive multi-turn requests completed successfully.

\- Latency was measured for each multi-turn request.



\## Context Retention Limitation



The current test environment uses `MockLLMProvider`.



The mock provider intentionally does not use conversation history when generating responses. Therefore, this evaluation verifies \*\*history transmission and conversation continuity at the API level\*\*, but it does not demonstrate semantic context retention by an actual language model.



True semantic context-retention testing should be performed when an actual history-aware LLM provider is enabled.



\## Conclusion



The Sept 16 multi-turn evaluation completed successfully with 4/4 automated tests passing.



All 9 consecutive chatbot requests returned valid responses with consistent JSON structure and preserved conversation identifiers. The measured average latency was 8.78 ms across the nine multi-turn requests.



The results represent local test-environment performance using FastAPI `TestClient` and `MockLLMProvider`; they should not be interpreted as production latency or real-world LLM performance.

