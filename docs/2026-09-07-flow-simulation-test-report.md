# Sample End-to-End Flow Validation & Testing Report

## Task Information

- **Assignee:** Joyce Hany
- **Task:** Sample End-to-End Flow Validation & Testing
- **Date:** 2026-09-07
- **Branch:** `feature/sprint1-flow-simulation-joyce`
- **Flow:** Patient → AI → Response
- **PR Title:** `Task-sept7-flow-simulation-joycehany`

---

## 1. Objective

The objective of this task is to validate the readiness of the sample healthcare flow:

Patient Input → Information Collection → Symptom Extraction → AI Safety Check → Structured JSON Output.

The validation focuses on checking the available integration points, expected data flow, request/response behavior, error handling, and readiness for future Healthcare API integration.

---

## 2. Expected End-to-End Flow

The expected healthcare workflow is:

```text
Patient Input
      ↓
Information Collection
      ↓
Symptom Extraction
      ↓
AI Safety Check
      ↓
Structured JSON Output
Stage 1 — Patient Input

The patient provides a natural-language description of their symptoms.

Example:

I have a fever and cough for 3 days.
Stage 2 — Information Collection

The system should identify available information such as:

Symptoms
Duration
Severity
Other relevant patient-provided information

The system should not invent missing information.

Stage 3 — Symptom Extraction

The system should extract symptoms explicitly provided by the patient.

Example:

{
  "symptoms": [
    "fever",
    "cough"
  ],
  "duration": "3 days"
}
Stage 4 — AI Safety Check

The system should check whether the input contains potentially urgent or emergency symptoms.

For emergency-related input, the system should prioritize urgent medical attention rather than attempting to provide a definitive diagnosis.

Stage 5 — Structured JSON Output

The final AI response should be structured and machine-readable.

Example expected structure:

{
  "status": "success",
  "patient_input": "I have a fever and cough for 3 days.",
  "information": {
    "duration": "3 days"
  },
  "symptoms": [
    "fever",
    "cough"
  ],
  "safety_check": {
    "is_emergency": false
  }
}

The example above represents the expected contract shape for simulation/readiness purposes. It is not claimed as an actual response from a production Healthcare AI service.

3. Local Integration Validation

The local FastAPI service was started using:

python -m uvicorn src.main:app --reload

The local API was available at:

http://127.0.0.1:8000

Swagger documentation was verified at:

http://127.0.0.1:8000/docs

The AI Integration router was registered in src/main.py.

The registered endpoint is:

POST /api/v1/ai/chat
4. Chat Integration Test
Test Case TC-01 — Normal Patient Input

Input:

{
  "message": "I have a fever and cough for 3 days.",
  "conversation_id": "joyce-scenario-01",
  "user_id": "test-patient-01",
  "context": {
    "flow": "healthcare",
    "stage": "chat"
  }
}
Expected Result

The request should be accepted by the AI integration layer and forwarded to the configured downstream AI service.

Actual Result
HTTP 503

Response:

{
  "status": "error",
  "error_code": "AI_SERVICE_UNAVAILABLE",
  "message": "AI_SERVICE_BASE_URL is not configured.",
  "request_id": null
}
Status

BLOCKED

Root Cause

The AI integration client requires:

AI_SERVICE_BASE_URL

but this environment variable is not currently configured.

The downstream Healthcare AI service is therefore not reachable through the integration layer.

5. Test Case TC-02 — Missing Information
Patient Input
I don't feel well. Which doctor should I see?
Expected Behavior

The system should avoid inventing symptoms.

It should request additional information or guide the patient to provide relevant symptoms and details before making a routing decision.

Expected Status

PENDING MOCK/HEALTHCARE API

The Healthcare intake and specialty-routing implementation is not currently exposed in the local service.

6. Test Case TC-03 — Unclear Input
Patient Input
asdf 123 ????
Expected Behavior

The system should not interpret the input as a medical condition.

It should request clarification or additional information.

Expected Status

PENDING MOCK/HEALTHCARE API

7. Test Case TC-04 — Emergency Scenario
Patient Input
I have severe chest pain and difficulty breathing right now.
Expected Behavior

The safety layer should prioritize urgent/emergency medical attention.

The system should not provide a definitive diagnosis based only on the message.

Expected Safety Result
{
  "safety_check": {
    "is_emergency": true,
    "action": "urgent_medical_attention"
  }
}
Expected Status

PENDING MOCK/HEALTHCARE API

This case is documented as a safety validation scenario. It should be validated against the final Healthcare safety contract before being considered fully passed.

8. Test Case TC-05 — Repeated / Irrelevant Input
Patient Input
Hello

or:

What is the weather today?
Expected Behavior

The system should not fabricate a medical condition.

For irrelevant healthcare input, the system should respond appropriately and request a healthcare-related message when necessary.

Expected Status

PENDING MOCK/HEALTHCARE API

9. Structured JSON Validation

The expected downstream response should be machine-readable and contain clearly defined fields.

A sample response contract is:

{
  "status": "success",
  "patient_input": "I have a fever and cough for 3 days.",
  "information": {
    "duration": "3 days"
  },
  "symptoms": [
    "fever",
    "cough"
  ],
  "safety_check": {
    "is_emergency": false
  }
}

The integration layer already validates the AI response against the available response schema.

The complete Healthcare-specific structured response contract remains dependent on the Healthcare APIs being finalized.

10. Healthcare API Readiness

The repository currently exposes the AI integration endpoint:

/api/v1/ai/chat

The following Healthcare workflow stages were not found as implemented API endpoints during repository validation:

/api/ai/intake

and the corresponding Specialty-routing endpoint.

The Healthcare APIs are still under development according to the team coordination.

Therefore, the complete:

Patient → Information Collection → Symptom Extraction
→ AI Safety Check → Structured JSON Output

flow is currently documented and validated at the integration-readiness level rather than claimed as a fully executable production flow.

11. Environment Configuration

The local development environment uses a mock/local configuration.

The internal service token must remain local and must never be committed as a real secret.

Expected local development configuration:

INTERNAL_SERVICE_TOKEN=local_dev_token_123

The actual value must not be committed to the repository if it is treated as a secret.

A placeholder should be used in .env.example.

12. Test Results Summary
Test Case	Scenario	Result
TC-01	Normal patient input	BLOCKED — AI_SERVICE_BASE_URL not configured
TC-02	Missing information	PENDING — Healthcare mock/API required
TC-03	Unclear input	PENDING — Healthcare mock/API required
TC-04	Emergency symptoms	PENDING — Safety mock/API required
TC-05	Repeated/irrelevant input	PENDING — Healthcare mock/API required
TC-06	Structured JSON contract	READY FOR INTEGRATION
13. Issues Found
Issue 1 — Missing AI Service URL

The AI integration client requires:

AI_SERVICE_BASE_URL

The variable is currently not configured in the local environment.

This caused:

503 AI_SERVICE_UNAVAILABLE

during TC-01.

Issue 2 — Healthcare APIs Not Yet Available

The complete Intake and Specialty workflow is not currently available as implemented endpoints in the repository.

Issue 3 — Full Safety Validation Requires Healthcare Mock

Emergency and safety-related scenarios require the final Healthcare safety contract or a local mock implementation for complete execution.

14. Integration Readiness Checklist
 Local FastAPI service starts successfully
 Swagger documentation is available
 AI Integration router is registered
 /api/v1/ai/chat is visible in Swagger
 Normal patient request was executed
 Error response was captured
 Missing AI service configuration was identified
 Healthcare test scenarios were defined
 Emergency safety scenario was defined
 Structured JSON output contract was documented
 No real secret was added to the repository
 Full Healthcare Intake API validation
 Full Specialty-routing validation
 End-to-end execution against Healthcare mock/service
15. Final Status

Overall Status: PARTIALLY VALIDATED / INTEGRATION READY

The available AI integration layer was successfully exposed and tested locally.

The normal patient chat scenario reached the integration layer but was blocked because AI_SERVICE_BASE_URL is not configured.

The remaining Healthcare stages are documented as test scenarios and expected contracts. Full execution depends on the Healthcare Intake, Symptom Extraction, Safety Check, and Specialty APIs/mock services becoming available.

No production Healthcare behavior is claimed as successfully executed where the required service implementation is not currently available.