\# Sept 13 - AI Endpoint Scenario Matrix \& Integration Regression



\## Assignee

Rimsha Mushtaq



\## Role

Benchmark Testing \& Evaluation Engineer



\## Endpoint

POST /api/v1/chatbot



\## Test Coverage



The Sept 13 evaluation covers real-world AI endpoint scenarios:



\- Incomplete input

\- Urgent symptoms

\- Multi-symptom queries

\- Edge-case text

\- AI integration regression checks

\- Response latency benchmarking



\## Validation Command



`python -m pytest .\\tests\\test\_sept13\_ai\_evaluation.py -v -s`



\## Scenario Matrix Results



The scenario matrix completed successfully.



\- Incomplete input: HTTP 422 as expected from request validation

\- Urgent symptoms: HTTP 200

\- Multi-symptom query: HTTP 200

\- Edge-case text: HTTP 200



All successful responses were validated using the project's `ChatbotResponse` Pydantic schema.



\## AI Integration Regression



Previously relevant integration behavior was checked using representative normal, symptom-related, and off-topic queries.



\- Regression checks: 3/3 passed

\- HTTP response validation: successful

\- Conversation ID preservation: successful

\- Reply/source type validation: successful



No regression was observed in the tested endpoint behavior.



\## Latency Benchmark



\- Samples: 4

\- Average latency: 26.79 ms

\- Minimum latency: 9.62 ms

\- Maximum latency: 74.88 ms



Latency was measured using the local FastAPI `TestClient`. These values represent local benchmark timing and should not be interpreted as production external-LLM latency.



\## Findings



The endpoint correctly rejected incomplete input according to its request validation rules and successfully handled the tested urgent, multi-symptom, and edge-case scenarios.



The regression suite confirmed expected response structure and conversation ID handling for representative requests.



The urgent-symptom scenario was evaluated for API handling and integration behavior only. This benchmark does not establish clinical safety or medical correctness.



\## Conclusion



The Sept 13 evaluation successfully verifies the required real-world scenario matrix, regression behavior, and latency measurement for the tested AI endpoint.

