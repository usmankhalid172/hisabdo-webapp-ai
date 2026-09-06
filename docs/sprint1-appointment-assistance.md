# Sprint 1 — Appointment Assistance Module

## 1. Overview

The Appointment Assistance Module provides conversational guidance for common patient appointment requests.

The module identifies a patient's appointment-related intent and returns an appropriate conversational response together with a proposed backend API contract.

The current implementation supports:

* Doctor availability inquiries
* Appointment booking requests
* Appointment rescheduling requests
* Unknown or unsupported appointment-related requests

The module is designed to be backend-ready. The appointment API endpoints described in this document are **proposed API contracts only**. No appointment backend API integration is currently implemented in this repository.

---

## 2. Objective

The objective of this module is to provide a clear conversational workflow for patients who want to:

1. Check a doctor's availability.
2. Book an appointment.
3. Reschedule an existing appointment.

The module maps detected patient intents to proposed backend appointment operations so that a future backend integration can use the defined contract.

---

## 3. Module Structure

The Appointment Assistance implementation is organized as follows:

```text
src/
└── appointment_assistance/
    ├── __init__.py
    ├── intents.py
    ├── workflow.py
    └── api_contract.py

tests/
└── test_appointment_assistance.py

docs/
└── sprint1-appointment-assistance.md
```

### File Responsibilities

#### `intents.py`

Contains:

* `AppointmentIntent` enum
* Appointment intent keywords
* `detect_intent()` function
* Input validation
* Intent classification logic

#### `workflow.py`

Contains:

* `AppointmentWorkflowResult`
* Conversational responses
* Appointment message processing
* Intent-to-API-contract mapping

#### `api_contract.py`

Contains:

* Proposed appointment endpoint definitions
* HTTP methods
* Endpoint paths
* Endpoint descriptions
* `get_api_contract()` lookup function

#### `test_appointment_assistance.py`

Contains automated tests for:

* Intent detection
* Input validation
* Conversational workflows
* API contract mapping

---

## 4. Supported Intents

The module defines four appointment intents.

| Intent                   | Description                                                             |
| ------------------------ | ----------------------------------------------------------------------- |
| `doctor_availability`    | Patient wants to know whether a doctor has available appointment slots. |
| `book_appointment`       | Patient wants to schedule or book a new appointment.                    |
| `reschedule_appointment` | Patient wants to change the date or time of an existing appointment.    |
| `unknown`                | Patient's request does not match a supported appointment intent.        |

---

## 5. Intent Detection

The `detect_intent()` function accepts a patient's natural-language message and determines the primary appointment intent.

The message is normalized by:

* Converting text to lowercase.
* Removing leading and trailing whitespace.
* Normalizing repeated whitespace.

The function also validates that the input is a non-empty string.

### Intent Priority

Rescheduling is checked before the other intents because a rescheduling request may also contain generic appointment or booking-related words.

The detection order is:

```text
Reschedule
    ↓
Doctor Availability
    ↓
Book Appointment
    ↓
Unknown
```

### Examples

```text
"Is Dr. Ahmed available tomorrow?"
→ doctor_availability
```

```text
"I want to book an appointment with Dr. Ahmed."
→ book_appointment
```

```text
"I need to reschedule my appointment."
→ reschedule_appointment
```

```text
"What are your hospital timings?"
→ unknown
```

---

## 6. Conversational Workflow

The workflow connects the patient's message, detected intent, conversational guidance, and proposed API contract.

```text
Patient Message
      │
      ▼
Input Validation
      │
      ▼
Intent Detection
      │
      ▼
Appointment Intent
      │
      ├── doctor_availability
      │         │
      │         ▼
      │   Availability Guidance
      │         │
      │         ▼
      │   Proposed Availability API
      │
      ├── book_appointment
      │         │
      │         ▼
      │   Booking Guidance
      │         │
      │         ▼
      │   Proposed Booking API
      │
      ├── reschedule_appointment
      │         │
      │         ▼
      │   Rescheduling Guidance
      │         │
      │         ▼
      │   Proposed Rescheduling API
      │
      └── unknown
                │
                ▼
          General Guidance
```

The main workflow function is:

```python
process_appointment_message(message)
```

It returns an `AppointmentWorkflowResult` containing:

* Detected intent
* Conversational response
* Associated API contract, when applicable

---

## 7. Conversational Guidance

### 7.1 Doctor Availability

Example patient request:

```text
Is Dr. Ahmed available tomorrow?
```

Detected intent:

```text
doctor_availability
```

Response:

```text
I can help you check a doctor's available appointment slots.
Please provide the doctor's name and your preferred date.
```

The workflow expects the patient to provide the information required to perform an availability lookup.

---

### 7.2 Book Appointment

Example patient request:

```text
I want to book an appointment with Dr. Ahmed.
```

Detected intent:

```text
book_appointment
```

Response:

```text
I can help you book an appointment.
Please provide the doctor's name and your preferred date and time.
```

The workflow guides the patient toward providing the information required for a future appointment booking request.

---

### 7.3 Reschedule Appointment

Example patient request:

```text
I need to reschedule my appointment.
```

Detected intent:

```text
reschedule_appointment
```

Response:

```text
I can help you reschedule your appointment.
Please provide your appointment ID and your preferred new date and time.
```

The workflow requests the appointment identifier and the new preferred appointment details.

---

### 7.4 Unknown Request

Example:

```text
What are your hospital timings?
```

Detected intent:

```text
unknown
```

Response:

```text
I can help with doctor availability, booking appointments,
or rescheduling appointments. Please tell me what you would like to do.
```

Unknown requests do not receive an appointment API contract.

---

## 8. Proposed Backend API Contracts

The following API contracts are defined to provide a clear interface for future backend integration.

**Important:** These endpoints are **proposed contracts**. They are not existing backend endpoints in the current repository.

| Intent                   | Method | Proposed Endpoint                | Purpose                                                  |
| ------------------------ | ------ | -------------------------------- | -------------------------------------------------------- |
| `doctor_availability`    | GET    | `/appointments/availability`     | Check available appointment slots for a doctor and date. |
| `book_appointment`       | POST   | `/appointments`                  | Create a new doctor appointment.                         |
| `reschedule_appointment` | PATCH  | `/appointments/{appointment_id}` | Change the date or time of an existing appointment.      |
| `unknown`                | —      | —                                | No appointment API mapping.                              |

### API Contract Example

For:

```text
doctor_availability
```

the proposed contract is:

```text
Method: GET
Path: /appointments/availability
Purpose: Check available appointment slots for a doctor and date.
```

For:

```text
book_appointment
```

the proposed contract is:

```text
Method: POST
Path: /appointments
Purpose: Create a new doctor appointment.
```

For:

```text
reschedule_appointment
```

the proposed contract is:

```text
Method: PATCH
Path: /appointments/{appointment_id}
Purpose: Change the date or time of an existing appointment.
```

---

## 9. Backend Integration Status

The current repository does not contain an existing appointment backend API.

Therefore, this Sprint 1 implementation does **not** make actual HTTP requests to an appointment service.

Instead, the module provides a clean contract that can be connected to the backend when the backend endpoints become available.

Current status:

```text
Intent detection              COMPLETE
Conversational workflow       COMPLETE
API contract definition       COMPLETE
API mapping                   COMPLETE
Automated tests               COMPLETE
Actual backend integration    NOT YET IMPLEMENTED
```

This separation allows the conversational logic to be developed independently of the backend implementation.

---

## 10. Input Validation

The `detect_intent()` function rejects invalid input.

### Empty message

An empty string raises:

```text
ValueError
```

### Non-string message

A non-string value also raises:

```text
ValueError
```

This prevents invalid patient messages from entering the intent detection workflow.

---

## 11. Testing

The Appointment Assistance test suite contains 13 automated tests.

### Intent Detection Tests

The tests verify:

* Doctor availability detection
* Booking detection
* Rescheduling detection
* Unknown intent detection
* Empty message rejection
* Non-string input rejection

### Workflow Tests

The tests verify:

* Availability workflow
* Booking workflow
* Rescheduling workflow
* Unknown workflow
* Correct API method mapping
* Correct API endpoint mapping

### Test Result

The complete Appointment Assistance test suite was executed using:

```bash
pytest tests/test_appointment_assistance.py -v
```

Result:

```text
13 passed in 0.14s
```

All tests passed successfully.

---

## 12. Example End-to-End Flow

### Availability Example

```text
Patient:
"Is Dr. Ahmed available tomorrow?"

        ↓

Intent Detection

        ↓

doctor_availability

        ↓

Conversational Guidance:
"I can help you check a doctor's available appointment slots.
Please provide the doctor's name and your preferred date."

        ↓

Proposed API Contract:

GET /appointments/availability
```

### Booking Example

```text
Patient:
"I want to book an appointment with Dr. Ahmed."

        ↓

Intent Detection

        ↓

book_appointment

        ↓

Conversational Guidance:
"I can help you book an appointment.
Please provide the doctor's name and your preferred date and time."

        ↓

Proposed API Contract:

POST /appointments
```

### Rescheduling Example

```text
Patient:
"I need to reschedule my appointment."

        ↓

Intent Detection

        ↓

reschedule_appointment

        ↓

Conversational Guidance:
"I can help you reschedule your appointment.
Please provide your appointment ID and your preferred new date and time."

        ↓

Proposed API Contract:

PATCH /appointments/{appointment_id}
```

---

## 13. Limitations and Future Work

The current implementation is intentionally focused on conversational intent detection and workflow guidance.

Future work can include:

1. Connecting the proposed contracts to actual backend appointment endpoints.
2. Extracting doctor names from patient messages.
3. Extracting dates and times from natural-language requests.
4. Validating appointment IDs.
5. Calling the availability service and returning real appointment slots.
6. Creating booking requests through the backend.
7. Updating existing appointments through the backend.
8. Handling unavailable slots and backend errors.
9. Adding authentication and patient identity handling where required.
10. Adding integration tests once backend endpoints are available.

---

## 14. Summary

The Sprint 1 Appointment Assistance Module provides a structured foundation for appointment-related conversational interactions.

It currently supports:

```text
Patient Message
      ↓
Intent Detection
      ↓
Conversational Guidance
      ↓
Proposed API Contract
```

The implementation has been tested with 13 automated tests, all of which pass successfully.

The backend appointment endpoints are currently treated as **proposed contracts only** because no appointment API implementation or specification is available in the repository at this stage.
