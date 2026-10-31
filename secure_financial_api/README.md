# Secure Financial API and Semantic Knowledge Retrieval

## 1. Project Overview

This project contains a learning implementation of a secure financial API and a prototype for semantic knowledge retrieval for the HisabDo financial assistant.

It demonstrates authentication and authorization checks, account-level data isolation, reporting-period validation, semantic FAQ retrieval, source attribution, and safe fallback behavior.

## 2. Secure Financial API

### Features

- Authentication and token validation.
- Authorization checks to restrict access to account-specific financial data.
- Cross-customer access protection.
- Separation of demo and actual financial data.
- Reporting-period validation.
- Validation of request parameters and data modes.
- Automated security regression tests.

### Reporting Periods

- `start_date` is inclusive.
- `end_date` is exclusive.

For example, a request with `start_date=2026-10-01` and `end_date=2026-11-01` covers October 2026, including October 31 but excluding November 1.

### Local Setup

From the repository root, create and activate a virtual environment if you have not already done so:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project's requirements:

```powershell
python -m pip install -r .\secure_financial_api\requirements.txt
```

Set a local JWT secret for testing:

```powershell
$env:JWT_SECRET = "replace-with-a-long-random-secret-for-local-testing"
```

Start the API:

```powershell
python -m uvicorn app:app --app-dir secure_financial_api --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

### Demo Tokens

The local demo endpoint can issue tokens for sample users such as `alice`, `bob`, and `admin`.

Example request body:

```json
{
  "username": "alice"
}
```

**Important:** The demo-token endpoint is for local learning and testing only. It must not be exposed as an unauthenticated token-issuing endpoint in production.

### Example Financial Summary Request

```http
GET /financial-summary?data_mode=actual&start_date=2026-10-01&end_date=2026-11-01
```

The request must include a valid authorization token. The API should enforce account-level access restrictions and validate the requested reporting period.

Sample amounts in this learning implementation are test data, not real customer financial information.

## 3. Semantic Knowledge Retrieval Prototype

### Purpose

The retrieval prototype searches a small FAQ knowledge base for information relevant to a user's question. It is intended to improve retrieval when users phrase similar questions in different ways.

### Main Components

- `knowledge_retrieval.py` - retrieval implementation.
- `knowledge_base/faq.json` - FAQ knowledge base.
- `test_knowledge_retrieval.py` - retrieval evaluation checks.

The prototype uses the multilingual sentence-transformer model:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

The configured relevance threshold is `0.45`. Retrieval quality depends on the knowledge-base content, model behavior, and threshold, so this value should be evaluated against representative questions before production use.

### Retrieval Behaviors Evaluated

- Questions about receivables and money owed by customers.
- Questions about payables.
- Different wording for similar questions.
- Roman Urdu and English mixed-language questions.
- Source identification for retrieved FAQ answers.
- Safe fallback when a question is unrelated to the available knowledge base.

### Run the Retrieval Evaluation

From the repository root:

```powershell
python -m pytest secure_financial_api/test_knowledge_retrieval.py -v
```

The verified local run reported **1 pytest test function passed**. That function evaluates six scenarios and 18 individual checks.

To run the evaluation script directly and view its scenario-by-scenario output:

```powershell
python .\secure_financial_api\test_knowledge_retrieval.py
```

### Source Attribution and Fallback

Retrieved answers should identify the source FAQ or document when applicable. If no sufficiently relevant source is found, the system should use a safe fallback instead of presenting an unsupported answer as fact.

A successful test run demonstrates that the tested scenarios passed; it does not prove that every FAQ is officially verified or that every possible user question will be handled correctly.

### Important Integration Limitation

The semantic retrieval prototype is not, by itself, proof that the live HisabDo chatbot uses this retrieval pipeline.

Personalized balances, receivables, payables, and transaction summaries must come from authenticated, account-scoped financial APIs. Static FAQ retrieval must not be used to invent or replace a user's actual financial data.

## 4. Security Regression Tests

From the repository root, run:

```powershell
python -m pytest secure_financial_api/test_security.py -v
```

The verified local run reported **11 security tests passed**.

The tests cover authentication requirements, account isolation, account-ID tampering, demo-versus-actual data separation, reporting-period boundaries, invalid date ranges, token validation, expired tokens, and invalid data modes.

Test results apply to the code and environment at the time of the run. Run the tests again after making changes.

## 5. Production Security Limitations

This is a learning implementation, not a production-ready financial service.

Before production use:

- Replace sample in-memory records with a properly secured database.
- Use a trusted identity and authentication system.
- Disable or secure the demo-token endpoint.
- Store secrets securely and use strong, randomly generated signing keys.
- Enforce account-level authorization on every relevant endpoint.
- Use HTTPS, appropriate rate limiting, and audit logging.
- Review error handling, logging, data retention, and privacy controls.
- Test role permissions and cross-account isolation.
- Obtain a security review before connecting real financial data.

## 6. Current Verification Status

The following checks passed in the reported local runs:

| Area | Result |
|---|---|
| Security regression suite | 11 tests passed |
| Semantic retrieval evaluation | 1 pytest test function passed |
| Retrieval scenarios | 6 scenarios evaluated |
| Individual retrieval checks | 18 checks passed |

These results do not establish that the live Groq API integration or the live HisabDo chatbot integration is working. Those require separate integration tests.

## 7. Next Steps

1. Review and verify the FAQ content against approved product documentation.
2. Evaluate the retrieval threshold against a broader test set.
3. Expand English and Roman Urdu regression coverage.
4. Investigate retrieval failures and document their root causes.
5. Verify live LLM integration independently from unit tests.
6. Confirm that personalized financial answers use authenticated account-specific data.
7. Run the relevant tests again after each code change.


