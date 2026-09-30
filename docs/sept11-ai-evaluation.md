# Sept 11 - AI Endpoint Evaluation & JSON Consistency

## Assignee
Rimsha Mushtaq

## Role
Benchmark Testing & Evaluation Engineer

## Endpoint
POST /api/v1/chatbot

## Test Coverage

The Sept 11 evaluation suite covers:

- Normal query
- Multiple symptoms
- Missing-information scenario
- Non-medical input
- Emergency case
- JSON response format consistency
- Response latency measurement

## Validation Command

`python -m pytest .\tests\test_sept11_ai_evaluation.py -v -s`

## Direct Endpoint Validation

The five required scenarios were manually validated against the local API.

All five returned HTTP 200 responses and valid `ChatbotResponse` payloads.

The emergency scenario was tested for API handling and payload validity. The test does not claim that the system provides clinical emergency guidance.

## JSON Consistency

Expected response fields:

- `reply`
- `conversation_id`
- `intent`
- `tokens_used`
- `source`

Responses are validated using the project's `ChatbotResponse` Pydantic schema.

## Latency

Latency is measured using local FastAPI `TestClient` end-to-end timing.

These measurements are local benchmark results and should not be interpreted as production external-LLM latency.

## Result

The automated Sept 11 evaluation suite verifies successful API handling, JSON schema consistency, and latency measurement across the required scenarios.
