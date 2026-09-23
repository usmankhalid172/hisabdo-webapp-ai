\# Sept 12 - Comprehensive AI Endpoint Evaluation



\## Assignee

Rimsha Mushtaq



\## Role

Benchmark Testing \& Evaluation Engineer



\## Endpoint

POST /api/v1/chatbot



\## Test Coverage



The Sept 12 evaluation suite covers diverse patient conversation scenarios:



\- Vague symptoms

\- Multiple symptoms

\- Emergency trigger

\- Off-topic input

\- JSON structural accuracy

\- Sequential latency benchmarking

\- Concurrent endpoint stability



\## Validation Command



`python -m pytest .\\tests\\test\_sept12\_ai\_evaluation.py -v -s`



\## Results



The automated evaluation suite completed successfully.



\- Tests passed: 4/4

\- HTTP response validation: Successful

\- JSON schema validation: Successful

\- Scenario coverage: Successful

\- Concurrent endpoint stability: Successful



\## Latency Benchmark



Sequential benchmark:



\- Samples: 4

\- Average latency: 6.65 ms

\- Minimum latency: 5.80 ms

\- Maximum latency: 7.00 ms



Concurrent benchmark:



\- Concurrent requests: 4

\- Average latency: 21.71 ms

\- Minimum latency: 20.51 ms

\- Maximum latency: 22.76 ms



\## JSON Structural Accuracy



Each response was validated against the project's `ChatbotResponse` Pydantic schema.



Expected response fields:



\- `reply`

\- `conversation\_id`

\- `intent`

\- `tokens\_used`

\- `source`



All tested responses passed structural validation.



\## Findings



The tested endpoint successfully handled vague symptom descriptions, multi-symptom complaints, emergency-trigger wording, and off-topic input while maintaining the expected response structure.



The emergency scenario was evaluated for API handling and JSON structural validity only. This benchmark does not claim clinical safety or medical correctness.



Latency measurements were collected using the local FastAPI `TestClient`. They represent local benchmark timing and should not be interpreted as production external-LLM latency.



\## Conclusion



The Sept 12 evaluation confirms successful automated scenario coverage, JSON structural validation, latency measurement, and concurrent endpoint stability for the tested AI endpoint.

