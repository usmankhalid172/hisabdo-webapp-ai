# Secure Financial API (Learning Implementation)

## What this demonstrates

* Authentication: protected routes require a signed, unexpired bearer token.
* Authorization: account scope is taken from verified token claims and checked against the server-side user/account association.
* Cross-customer isolation: each query filters records by the authenticated account.
* Demo vs. actual data: every query explicitly selects `demo` or `actual`; modes are filtered separately.
* Reporting periods: `start\_date` is inclusive and `end\_date` is exclusive (`\[start\_date, end\_date)`).
* Input validation: invalid or overly long date ranges are rejected.
* Security tests: missing/invalid token, cross-account isolation, account ID tampering, demo/actual separation, and date boundaries.

## Important limitations

This is a teaching sample, not production-ready financial software:

* It uses in-memory sample records and demo identities.
* `/demo-token` has no password verification and MUST be removed/disabled in production.
* The local fallback JWT secret is only for learning. Production must fail startup if a secure secret is not configured.
* Replace the demo users and records with a database and enforce account ownership in every database query.
* Use your organization's real identity provider, secure password hashing where applicable, HTTPS, audit logging, rate limiting, secret management, and appropriate access controls.
* Add authorization rules for multi-user businesses/roles if the real product supports them.
* Do not connect this example to real financial data without a proper security review.

## Setup

Use Python 3.10+.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
$env:JWT\_SECRET = "replace-with-a-long-random-secret-for-local-testing"
uvicorn app:app --reload
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
export JWT\_SECRET="replace-with-a-long-random-secret-for-local-testing"
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the API.

## Get a local demo token

POST `/demo-token` with JSON:

```json
{"username":"alice"}
```

Available sample usernames: `alice`, `bob`, `admin`. This route is for local testing only.

Copy the `access\_token` from the response. In `/docs`, click **Authorize** and enter:
`Bearer YOUR\_TOKEN`

## Example request

`GET /financial-summary?data\_mode=actual\&start\_date=2026-10-01\&end\_date=2026-11-01`

With Alice's token, the sample actual summary is:

* Receivables: PKR 1,200
* Payables: PKR 300

The demo summary is separate and shows demo receivables of PKR 9,999.

## Run security tests

Run the automated security test suite from the project folder:

```bash
python -m pytest -q
```

The test suite currently contains 11 tests covering:

* Authentication required for protected endpoints
* Cross-account financial data isolation
* Account ID tampering prevention
* Demo and actual data separation
* Inclusive start date and exclusive end date
* Invalid date range rejection
* Invalid token rejection
* Unknown username rejection
* Date ranges exceeding 366 days
* Expired token rejection
* Invalid data mode rejection

All 11 tests passed during local testing.

**Note:** Test results may change if the code or environment changes. These tests cover specific scenarios and do not guarantee complete security.

```

## Reporting-period rule
The API treats the start date as included and the end date as excluded. For the whole month of October, use:
`start\_date=2026-10-01\&end\_date=2026-11-01`
This avoids double-counting records that fall exactly on adjacent period boundaries.



\## Semantic Knowledge Retrieval Prototype



\### What this demonstrates



\- Multilingual semantic search using sentence embeddings.

\- Relevance threshold of 0.45.

\- Source attribution for retrieved FAQ entries.

\- Safe fallback when no sufficiently relevant answer is found.

\- A versioned JSON knowledge base.



\### Evaluation results



The local retrieval evaluation currently includes six test cases:

\- Receivable definition.

\- Payable definition.

\- Customer debt expressed in different wording.

\- Safe fallback for an unrelated question.

\- Urdu-English mixed-language question.

\- Outstanding customer debt question.



The enhanced evaluation checks answer presence, source presence, expected FAQ retrieval, and safe fallback behaviour.



\*\*Latest local result:\*\* 6/6 test cases passed and 18/18 individual checks passed.



\### Root Cause Analysis



The file `root\_cause\_analysis.md` records observed chatbot issues, likely causes, recommended fixes, and verification steps.



Root causes are preliminary hypotheses until confirmed through application logs, reproducible tests, and investigation of the live system.



\### Limitations



\- This is a retrieval prototype and is not integrated into the live HisabDo chatbot.

\- FAQ source details must be verified against official product documentation.

\- A source being present does not prove that its content is officially verified.

\- Actual customer balances must be retrieved from authenticated, account-scoped financial APIs, not inferred from FAQ search.

\- Live chatbot behaviour must be tested separately before claiming an issue is resolved.



\### Run retrieval evaluation



From the `secure\_financial\_api` project folder:



```powershell

python test\_knowledge\_retrieval.py

```



\### Run security regression tests



```powershell

python -m pytest -q test\_security.py

```



The security test suite previously passed 11 tests during local testing. Test results should be confirmed again after relevant code changes.



