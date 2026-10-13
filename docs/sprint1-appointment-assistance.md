# Sprint 1 — Appointment Assistance Module

## 1. Overview

The Appointment Assistance Module provides conversational guidance for common patient appointment requests.

The module identifies a patient's appointment-related intent, collects the information required for the selected workflow, and returns an appropriate conversational response together with a proposed backend API contract.

The current implementation supports:

* Doctor availability inquiries
* Appointment booking requests
* Appointment rescheduling requests
* Patient information collection
* Multi-turn appointment conversations
* Unknown or unsupported appointment-related requests

The module is designed to be backend-ready. The appointment API endpoints described in this document are **proposed API contracts only**. No appointment backend API integration is currently implemented in this repository.

---

## 2. Objective

The objective of this module is to provide a structured conversational workflow for patients who want to:

1. Check a doctor's availability.
2. Book an appointment.
3. Reschedule an existing appointment.
4. Provide patient and appointment information required by the selected workflow.

The module maps detected patient intents to proposed backend appointment operations so that a future backend integration can use the defined contract.

---

## 3. Module Structure

The Appointment Assistance implementation is organized as follows:

```text
src/
└── appointment_assistance/
    ├── __init__.py
    ├── intents.py
    ├── patient_info.py
    ├── workflow.py
    └── api_contract.py

tests/
├── test_appointment_assistance.py
└── test_patient_info.py

data/
└── sprint1_intent_mapping_test_log.csv

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

#### `patient_info.py`

Contains:

* `PatientInformation` data structure
* `PatientInformationCollector`
* Patient name collection
* Doctor name extraction
* Preferred date extraction
* Preferred time extraction
* Appointment ID extraction
* Required-field validation
* Multi-turn information persistence

The collector uses deterministic regular-expression patterns for basic information extraction.

#### `workflow.py`

Contains:

* `AppointmentWorkflowResult`
* Conversational responses
* Appointment message processing
* Patient information collection
* Multi-turn intent persistence
* Missing-information detection
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
* Availability workflow
* Booking workflow
* Rescheduling workflow
* Multi-turn booking workflow
* Unknown requests
* API contract mapping

#### `test_patient_info.py`

Contains tests for:

* Patient information extraction
* Doctor extraction
* Date extraction
* Time extraction
* Appointment ID extraction
* Empty input validation
* Required-field detection
* Workflow readiness

#### `sprint1_intent_mapping_test_log.csv`

Contains representative intent-mapping test cases showing:

* Patient message
* Expected intent
* Detected intent
* Required information
* Proposed API method
* Proposed API endpoint
* Test result

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

## 6. Patient Information Collection

The `PatientInformationCollector` stores appointment information collected during the conversation.

The supported information fields are:

| Field            | Purpose                                                 |
| ---------------- | ------------------------------------------------------- |
| `patient_name`   | Identifies the patient for a booking workflow.          |
| `doctor_name`    | Identifies the requested doctor.                        |
| `preferred_date` | Stores the patient's preferred appointment date.        |
| `preferred_time` | Stores the patient's preferred appointment time.        |
| `appointment_id` | Identifies an existing appointment during rescheduling. |

### Example Extraction

For the message:

```text
"My name is Mehar and I want to book an appointment
with Dr. Ahmed on Monday at 10 AM."
```

The collector can extract:

```text
patient_name   = Mehar
doctor_name    = Dr. Ahmed
preferred_date = Monday
preferred_time = 10 AM
```

For:

```text
"I want to reschedule appointment APT-123
to Monday at 10 AM."
```

The collector can extract:

```text
appointment_id = APT-123
preferred_date = Monday
preferred_time = 10 AM
```

### Important Availability Rule

A patient's preferred date or time is treated as a **preference**, not as a confirmed appointment slot.

For example:

```text
Patient:
"Book Monday at 10 AM."
```

does **not** mean that Monday at 10 AM is available.

The correct workflow is:

```text
Patient preference
        ↓
Check actual backend availability
        ↓
Return available slots
        ↓
Patient selects a slot
        ↓
Confirm/book appointment
```

Actual appointment availability must come from the backend appointment system once integration is implemented.

---

## 7. Required Information by Intent

Different appointment workflows require different information.

### Doctor Availability

Required:

```text
doctor_name
```

Preferred information:

```text
preferred_date
preferred_time
```

Preferred date/time are optional because the patient may ask for the doctor's next available slot.

Example:

```text
"When is Dr. Ahmed available?"
```

The workflow can proceed with the doctor name and request actual availability from the backend.

---

### Book Appointment

Required:

```text
patient_name
doctor_name
```

Optional preferences:

```text
preferred_date
preferred_time
```

The preferred date/time are not treated as confirmed slots.

---

### Reschedule Appointment

Required:

```text
appointment_id
```

Optional preferences:

```text
preferred_date
preferred_time
```

The new date/time are treated as requested preferences until actual availability is checked.

---

## 8. Conversational Workflow

The workflow connects the patient's message, intent detection, information collection, missing-field handling, conversational guidance, and proposed API contract.

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
Patient Information Extraction
      │
      ▼
Update Conversation State
      │
      ▼
Check Required Information
      │
      ├── Information Missing
      │        │
      │        ▼
      │   Ask Patient for Missing Information
      │
      └── Information Complete
               │
               ▼
        Proposed API Contract
               │
               ▼
       Future Backend Integration
```

The main workflow function is:

```python
process_appointment_message(message)
```

A shared `PatientInformationCollector` can also be supplied to maintain information across multiple conversation turns.

The returned `AppointmentWorkflowResult` contains:

* Detected intent
* Conversational response
* Associated API contract, when applicable
* Collected patient information
* Missing required fields

---

## 9. Multi-Turn Conversation

The workflow supports collecting information across multiple patient messages.

### Example

First patient message:

```text
"I want to book an appointment with Dr. Ahmed."
```

The system detects:

```text
Intent:
book_appointment

Collected:
doctor_name = Dr. Ahmed

Missing:
patient_name
```

The system responds:

```text
May I have your name?
```

Second patient message:

```text
"My name is Mehar and I prefer Monday at 10 AM."
```

The existing conversation state is retained:

```text
patient_name   = Mehar
doctor_name    = Dr. Ahmed
preferred_date = Monday
preferred_time = 10 AM
```

The workflow can then proceed to the availability-checking stage.

This allows the patient to provide information naturally rather than requiring all information in a single message.

---

## 10. Conversational Guidance

### 10.1 Doctor Availability

Example patient request:

```text
Is Dr. Ahmed available tomorrow?
```

Detected intent:

```text
doctor_availability
```

The workflow extracts:

```text
doctor_name    = Dr. Ahmed
preferred_date = tomorrow
```

Response:

```text
Thank you. I have your doctor and preferred date.
The next step is to check the doctor's actual available slots.
```

The system does not assume that the requested date is available.

---

### 10.2 Book Appointment

Example patient request:

```text
I want to book an appointment with Dr. Ahmed.
```

Detected intent:

```text
book_appointment
```

The workflow recognizes:

```text
doctor_name = Dr. Ahmed
```

and identifies the missing required field:

```text
patient_name
```

Response:

```text
May I have your name?
```

After the patient provides their name and optional appointment preferences, the workflow can proceed to checking actual availability.

For example:

```text
My name is Mehar and I prefer Monday at 10 AM.
```

The workflow stores:

```text
patient_name   = Mehar
doctor_name    = Dr. Ahmed
preferred_date = Monday
preferred_time = 10 AM
```

The response is:

```text
Thank you. I have your appointment preferences.
The next step is to check the doctor's actual availability before confirming a slot.
```

---

### 10.3 Reschedule Appointment

Example patient request:

```text
I need to reschedule my appointment.
```

Detected intent:

```text
reschedule_appointment
```

The workflow identifies that the appointment ID is missing.

Response:

```text
Please provide your appointment ID.
```

For:

```text
I want to reschedule appointment APT-123 to Monday at 10 AM.
```

The workflow extracts:

```text
appointment_id = APT-123
preferred_date = Monday
preferred_time = 10 AM
```

The response is:

```text
Thank you. I have your new appointment preference.
The next step is to check availability before confirming the rescheduled slot.
```

---

### 10.4 Unknown Request

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

## 11. Proposed Backend API Contracts

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

Purpose:
Check available appointment slots for a doctor and date.
```

For:

```text
book_appointment
```

the proposed contract is:

```text
Method: POST
Path: /appointments

Purpose:
Create a new doctor appointment.
```

For:

```text
reschedule_appointment
```

the proposed contract is:

```text
Method: PATCH
Path: /appointments/{appointment_id}

Purpose:
Change the date or time of an existing appointment.
```

---

## 12. Backend Integration Status

The current repository does not contain an existing appointment backend API.

Therefore, this Sprint 1 implementation does **not** make actual HTTP requests to an appointment service.

Instead, the module provides a clean conversational workflow and API contract that can be connected to the backend when the backend endpoints become available.

Current status:

```text
Intent detection                 COMPLETE
Patient information collection  COMPLETE
Basic information extraction     COMPLETE
Multi-turn workflow              COMPLETE
Conversational guidance          COMPLETE
API contract definition          COMPLETE
API mapping                      COMPLETE
Automated tests                  COMPLETE
Intent mapping test log          COMPLETE
Actual backend integration       NOT YET IMPLEMENTED
```

This separation allows the conversational logic to be developed independently of the backend implementation.

---

## 13. Input Validation

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

The patient information collector applies the same basic validation to incoming messages.

This prevents invalid patient messages from entering the conversational workflow.

---

## 14. Testing

The Appointment Assistance test suite currently contains **16 automated tests** in `test_appointment_assistance.py`.

A separate `test_patient_info.py` test suite validates the patient information collection and extraction functionality.

### Appointment Assistance Tests

The tests verify:

* Doctor availability detection
* Booking detection
* Rescheduling detection
* Unknown intent detection
* Empty message rejection
* Non-string input rejection
* Availability workflow
* Booking workflow
* Complete booking workflow
* Rescheduling workflow
* Complete rescheduling workflow
* Multi-turn booking workflow
* Unknown workflow
* Correct API method mapping
* Correct API endpoint mapping

### Patient Information Tests

The patient information tests verify:

* Patient name extraction
* Doctor name extraction
* Preferred date extraction
* Preferred time extraction
* Appointment ID extraction
* Input validation
* Missing required information
* Workflow readiness

### Test Result

The Appointment Assistance test suite was executed using:

```bash
pytest tests/test_appointment_assistance.py -v
```

Result:

```text
16 passed in 0.20s
```

All 16 Appointment Assistance tests passed successfully.

The patient information collector was also tested separately, with all 9 dedicated tests passing.

### Intent Mapping Test Log

Representative intent-mapping results are stored in:

```text
data/sprint1_intent_mapping_test_log.csv
```

The log contains test cases covering:

* Doctor availability
* Appointment booking
* Appointment rescheduling
* Unknown requests
* Multi-turn booking context
* Required information
* Proposed backend API mapping

All recorded test cases have a result of:

```text
PASS
```

---

## 15. Example End-to-End Flows

### Availability Example

```text
Patient:

"Is Dr. Ahmed available tomorrow?"

        ↓

Intent Detection

        ↓

doctor_availability

        ↓

Information Extraction

doctor_name = Dr. Ahmed
preferred_date = tomorrow

        ↓

Actual Availability Check
(Future backend integration)

        ↓

Proposed API Contract:

GET /appointments/availability
```

---

### Booking Example

```text
Patient:

"I want to book an appointment with Dr. Ahmed."

        ↓

Intent Detection

        ↓

book_appointment

        ↓

Information Collection

doctor_name = Dr. Ahmed
patient_name = missing

        ↓

System:

"May I have your name?"

        ↓

Patient:

"My name is Mehar and I prefer Monday at 10 AM."

        ↓

Information Collection

patient_name = Mehar
preferred_date = Monday
preferred_time = 10 AM

        ↓

Check Actual Doctor Availability

        ↓

Patient Selects Available Slot

        ↓

Future Booking API:

POST /appointments
```

---

### Rescheduling Example

```text
Patient:

"I want to reschedule appointment APT-123
to Monday at 10 AM."

        ↓

Intent Detection

        ↓

reschedule_appointment

        ↓

Information Extraction

appointment_id = APT-123
preferred_date = Monday
preferred_time = 10 AM

        ↓

Check Actual Availability

        ↓

Patient Confirms Available Slot

        ↓

Future Rescheduling API:

PATCH /appointments/{appointment_id}
```

---

## 16. Limitations and Future Work

The current implementation is intentionally focused on conversational intent detection, basic patient information collection, deterministic extraction, and workflow guidance.

Current limitations include:

1. Appointment API endpoints are proposed contracts only.
2. No real appointment backend requests are currently performed.
3. Information extraction uses simple deterministic patterns rather than an NLP/LLM extraction model.
4. Date extraction currently supports common relative dates, weekdays, and basic day-month formats.
5. Time extraction currently focuses on common AM/PM formats.
6. Appointment IDs are extracted using a basic expected format but are not validated against a real backend.
7. Doctor names are extracted using basic `Dr.` patterns.
8. Actual doctor availability cannot be confirmed until backend integration is available.

Future work can include:

1. Connecting the proposed contracts to actual backend appointment endpoints.
2. Improving natural-language doctor name extraction.
3. Adding robust date and time parsing.
4. Validating appointment IDs against the backend.
5. Calling the availability service and returning real appointment slots.
6. Allowing patients to select an available slot.
7. Creating booking requests through the backend.
8. Updating existing appointments through the backend.
9. Handling unavailable slots and backend errors.
10. Adding authentication and patient identity handling where required.
11. Adding integration tests once backend endpoints are available.
12. Adding more comprehensive conversational test cases.

---

## 17. Summary

The Sprint 1 Appointment Assistance Module provides a structured foundation for appointment-related conversational interactions.

The implemented workflow is:

```text
Patient Message
      ↓
Intent Detection
      ↓
Patient Information Collection
      ↓
Missing Information Check
      ↓
Conversational Guidance
      ↓
Availability / Booking / Rescheduling API Contract
      ↓
Future Backend Integration
```

The implementation currently supports:

```text
Doctor Availability
Appointment Booking
Appointment Rescheduling
Patient Information Collection
Basic Information Extraction
Multi-Turn Conversations
Intent-to-API Mapping
Intent Mapping Test Logging
Automated Testing
```

The Appointment Assistance test suite contains 16 automated tests, all of which pass successfully.

The patient information collector has an additional 9 dedicated tests, which also pass successfully.

The backend appointment endpoints are currently treated as **proposed contracts only** because no appointment API implementation or specification is available in the repository at this stage.
