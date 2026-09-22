# Sept 10 - AI Endpoint Evaluation & Payload Stability

## Assignee
Rimsha Mushtaq

## Role
Benchmark Testing & Evaluation Engineer

## Endpoint
POST /api/v1/chatbot

## Environment
Local development environment

## Test Coverage

The Sept 10 evaluation suite covers:

- Valid symptom scenario
- Multiple symptom scenario
- Missing message field
- Missing user_id field
- Missing conversation_id field
- Empty message
- Invalid message type
- Unsafe / prompt-injection-style input
- Response payload/schema stability
- Concurrent API calls

## Test Result

Command:

`python -m pytest .\tests\test_sept10_ai_evaluation.py -v -s`

Result:

- Total tests: 10
- Passed: 10
- Failed: 0
- Pass rate: 100%

## Concurrent Benchmark

- Concurrent requests: 10
- Workers: 5
- HTTP 200 responses: 10/10
- Schema-valid responses: 10/10
- HTTP success rate: 100%
- JSON schema validity: 100%
- Average latency: 29.81 ms
- Minimum latency: 22.81 ms
- Maximum latency: 39.68 ms

## Findings

All tested valid and edge-case scenarios completed successfully.

Missing and invalid request fields correctly returned HTTP 422 validation responses.

Unsafe/prompt-injection-style input did not break the API and returned a schema-valid response.

All concurrent requests returned HTTP 200 and produced responses compatible with the `ChatbotResponse` schema.

Latency measurements represent local FastAPI TestClient end-to-end timing and should not be interpreted as production external-LLM latency.

## Reproducibility

Run:

`python -m pytest .\tests\test_sept10_ai_evaluation.py -v -s`
