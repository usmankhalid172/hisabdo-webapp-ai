\# Sept 14 - AI Assistant Regression \& Concurrent Benchmark



\## Assignee

Rimsha Mushtaq



\## Role

Benchmark Testing \& Evaluation Engineer



\## Endpoint

POST /api/v1/chatbot



\## Test Coverage



The Sept 14 regression suite covers:



\- Full AI assistant regression scenarios

\- JSON payload structural consistency

\- Sequential response latency

\- Multi-user concurrent requests

\- Throughput measurement



\## Validation Command



`python -m pytest .\\tests\\test\_sept14\_ai\_regression.py -v -s`



\## Regression Results



\- Regression tests: 4/4 passed

\- JSON structural validation: passed

\- HTTP response validation: passed

\- Conversation ID validation: passed

\- Concurrent endpoint stability: passed



All tested successful responses were validated against the project's `ChatbotResponse` Pydantic schema.



\## Latency Benchmark



Sequential benchmark:



\- Samples: 6

\- Average latency: 6.46 ms

\- Minimum latency: 5.27 ms

\- Maximum latency: 8.71 ms



\## Concurrent Benchmark



Six simulated users were executed concurrently.



\- Concurrent users: 6

\- Total concurrent execution time: 38.23 ms

\- Average concurrent latency: 33.02 ms

\- Minimum concurrent latency: 32.23 ms

\- Maximum concurrent latency: 35.55 ms

\- Throughput: 156.93 requests/sec



All concurrent requests returned HTTP 200 and passed JSON schema validation.



\## JSON Payload Consistency



Expected response fields:



\- `reply`

\- `conversation\_id`

\- `intent`

\- `tokens\_used`

\- `source`



All tested responses contained the expected fields and passed Pydantic structural validation.



\## Findings



The AI assistant module successfully passed the representative regression suite. Concurrent multi-user calls completed successfully without response-status or JSON-structure failures.



Latency measurements were collected using the local FastAPI `TestClient`. These values represent local benchmark timing and should not be interpreted as production external-LLM latency.



\## Conclusion



The Sept 14 evaluation confirms successful regression coverage, JSON payload structural consistency, latency benchmarking, throughput measurement, and concurrent multi-user endpoint stability.

