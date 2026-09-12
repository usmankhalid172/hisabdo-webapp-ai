\# Doctor Information Assistant API Contract



\## Endpoint



`POST /api/v1/doctor-information`



The endpoint is protected by the shared `X-Internal-Token` header.



\## Request



```json

{

&#x20; "user\_id": "user-1",

&#x20; "question": "What is Dr. Ahmed Khan's specialty?",

&#x20; "conversation\_id": "doctor-c1"

}

### Request fields



| Field | Type | Required | Description |

|---|---|---|---|

| `user_id` | string | Yes | Application user's identifier |

| `question` | string | Yes | Doctor-information question |

| `conversation_id` | string | Yes | Conversation identifier |



## Successful response



```json

{

  "answer": "Based on the available doctor records:\nDoctor: Dr. Ahmed Khan\nSpecialty: Dermatology\nQualifications: MBBS, FCPS Dermatology\nSchedule: Monday: 10:00 AM - 2:00 PM, Wednesday: 10:00 AM - 2:00 PM, Friday: 2:00 PM - 6:00 PM",

  "conversation_id": "doctor-c1",

  "source": "doctor_knowledge_base",

  "retrieved": true,

  "retrieved_doctors": [

    "Dr. Ahmed Khan"

  ],

  "tokens_used": 35

}



### Response fields

| Field | Type | Description |
|---|---|---|
| `answer` | string | Grounded doctor-information response |
| `conversation_id` | string | Same conversation identifier supplied by the backend |
| `source` | string | Source/boundary that produced the response |
| `retrieved` | boolean | Whether approved doctor records were retrieved |
| `retrieved_doctors` | string[] | Names of doctors used as retrieval context |
| `tokens_used` | integer/null | LLM token usage when available |

## Unknown information

If the requested doctor information is not present:

```json
{
  "answer": "I couldn't find that information in the available doctor records.",
  "conversation_id": "doctor-c3",
  "source": "doctor_knowledge_base",
  "retrieved": false,
  "retrieved_doctors": [],
  "tokens_used": null
}



## Medical-advice boundary

Requests for diagnosis or treatment advice are blocked before the LLM is called.

Example response:

```json
{
  "answer": "I can provide doctor profile, specialty, qualification, and schedule information, but I can't provide diagnosis or treatment advice.",
  "conversation_id": "doctor-c2",
  "source": "doctor_information_safety_boundary",
  "retrieved": false,
  "retrieved_doctors": [],
  "tokens_used": null
}



## Authentication

The backend must send:

`X-Internal-Token: <configured internal service token>`

Missing or invalid authentication returns the shared service error contract:

```json
{
  "error_code": "UNAUTHORIZED_SERVICE",
  "message": "Missing or invalid internal service token",
  "request_id": "<request-id>"
}



## LLM configuration

The service uses the shared AI-service LLM configuration:

- `LLM_PROVIDER=mock`
- `LLM_PROVIDER=anthropic`
- `LLM_PROVIDER=openai`

Doctor-specific safety and grounding instructions are applied by the Doctor Information LLM boundary.

