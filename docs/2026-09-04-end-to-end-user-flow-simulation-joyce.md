# Sprint 1 – End-to-End User Flow Simulation Report

**Name:** Joyce Hany  
**Date:** 2026-09-07  
**Branch:** `feature/sprint1-flow-simulation-joyce`  
**Task:** End-to-End User Flow Simulation  
**Flow:** Chat → Intake → Specialty

## 1. Objective

The objective of this task was to validate the healthcare user flow and document the expected behavior, actual behavior, blockers, and safety scenarios.

The intended flow is:

Chat → Intake → Specialty

The Team Lead clarified that the deployed Healthcare APIs were still being set up and that the flow should be tested locally using a mocked/simulated pipeline.

## 2. Local Environment

Local service:

`http://127.0.0.1:8000`

Swagger:

`http://127.0.0.1:8000/docs`

The local FastAPI service started successfully using:

`python -m uvicorn src.main:app --reload`

## 3. Initial Testing

The deployed service was tested first.

The deployed Healthcare endpoint returned:

`HTTP 404 Not Found`

This was not treated as a code failure because the Team Lead confirmed that the Healthcare APIs were still being set up.

Testing was therefore moved to the local service.

## 4. AI Integration Endpoint

Repository inspection showed the AI integration router in:

`src/integration/routes.py`

The route is:

`POST /api/v1/ai/chat`

Initially, the endpoint returned 404 locally because the integration router was not registered in `src/main.py`.

### Resolution

The AI integration router was registered in the FastAPI application.

After restarting the service, Swagger displayed:

**AI Integration**

`POST /api/v1/ai/chat`

This confirmed that the application-facing AI integration route was successfully registered.

## 5. Case 01 – Normal Patient Journey

### Request

```json
{
  "message": "I have a fever and cough for 3 days.",
  "conversation_id": "joyce-scenario-01",
  "user_id": "test-patient-01",
  "context": {
    "flow": "healthcare",
    "stage": "chat"
  }
}
The expected healthcare flow is:

Chat → Intake → Specialty

The Chat stage should receive the patient's message and pass the relevant information to the next stage.

The Intake stage should collect missing information such as symptoms, duration, and severity.

The Specialty stage should use the collected information for appropriate routing.

Actual Result

The local request returned:

{
  "status": "error",
  "error_code": "AI_SERVICE_UNAVAILABLE",
  "message": "AI_SERVICE_BASE_URL is not configured.",
  "request_id": null
}

HTTP status:

503 Service Unavailable

Result

BLOCKED

The application-facing endpoint is available, but the downstream AI service URL is not configured.

This is a configuration/integration blocker rather than an invalid patient request.

6. Root Cause

Inspection of:

src/integration/client.py

showed that the AI integration client requires:

AI_SERVICE_BASE_URL

When this value is missing, the client raises:

AI_SERVICE_UNAVAILABLE

with:

AI_SERVICE_BASE_URL is not configured.

7. Resolution / Next Step

The Team Lead instructed the team to test the healthcare flow locally by mocking the pipeline because the Healthcare APIs were still being developed.

Therefore, the final Healthcare flow should be validated through the local mock:

Chat → Intake → Specialty

without depending on the unfinished deployed Healthcare endpoints.

8. Case 02 – Missing Information
Input
I don't feel well. Which doctor should I see?
Expected Behavior

The system should not immediately guess a specialty.

It should ask for additional information, such as:

Main symptoms
Duration
Severity
Other relevant information

The information should then be passed to the Intake stage.

Expected Result

The system asks clarification questions instead of making an unsupported specialty decision.

Status

Pending mock pipeline validation

9. Case 03 – Invalid / Unclear Input
Input
asdf 123 ????
Expected Behavior

The system should ask the user to provide clearer information.

It should not invent symptoms, diagnosis, or specialty.

Expected Result

Clarification request.

Status

Pending mock pipeline validation

10. Case 04 – Emergency / Safety
Input
I have severe chest pain and difficulty breathing right now.
Expected Behavior

The system should prioritize safety and recommend urgent/emergency medical attention.

It should not continue normal specialty routing as if the situation were routine.

It should also avoid claiming a definitive diagnosis.

Expected Result

Emergency escalation / urgent-care guidance.

Status

Safety scenario defined; final validation requires the Healthcare mock/contract.

11. Case 05 – Repeated / Irrelevant Input
Input
Hello
Hello
Hello

or:

What is the weather today?
Expected Behavior

The system should not fabricate a medical condition.

Repeated or irrelevant messages should be handled appropriately or redirected to the supported healthcare flow.

Expected Result

No fabricated symptoms, diagnosis, or specialty.

Status

Pending mock pipeline validation

12. API Contract Findings

The application-facing Chat request contains:

message
conversation_id
user_id
context

The normalized response contains:

status
response
request_id
sources
metadata

The integration client supports:

AI_SERVICE_BASE_URL
AI_SERVICE_CHAT_PATH
AI_SERVICE_API_KEY
AI_SERVICE_TIMEOUT
13. Healthcare Endpoint Findings

The current repository does not expose the complete Healthcare pipeline requested by the Team Lead.

The following were not found as implemented Healthcare endpoints:

/api/ai/intake

Specialty endpoint

Therefore, the complete:

Chat → Intake → Specialty

flow cannot currently be executed against real Healthcare endpoints.

The Team Lead's local mock/simulation approach is required until those services are available.

14. Security

The Team Lead provided the following local development token:

INTERNAL_SERVICE_TOKEN=local_dev_token_123

This must only be used for local development/testing.

No real secret or production credential should be committed to GitHub.

The .env.example file should contain a placeholder rather than a real secret.

15. Problems Encountered and Resolutions
Problem 1

Deployed Healthcare endpoint returned 404.

Resolution: Testing moved to the local service because the Team Lead confirmed the Healthcare APIs were still being set up.

Problem 2

/api/v1/ai/chat initially returned 404 locally.

Resolution: The AI integration router was registered in src/main.py.

Problem 3

Chat request returned 503.

Cause: AI_SERVICE_BASE_URL was not configured.

Resolution: The Team Lead instructed the team to use a local mocked/simulated pipeline rather than depending on the unfinished Healthcare service.

Problem 4

Intake and Specialty endpoints are not implemented in the current repository.

Resolution: Documented them as pending and defined the expected behavior for the simulated flow.

16. Final Status

The local AI integration route was successfully exposed and tested.

The normal healthcare Chat request reached the integration layer but was blocked at the downstream AI-service boundary because AI_SERVICE_BASE_URL was not configured.

The complete Healthcare flow is currently pending the mock pipeline / Healthcare service contracts.

The expected test scenarios and safety requirements have been documented for:

Normal patient journey
Missing information
Invalid/unclear input
Emergency/safety
Repeated/irrelevant input