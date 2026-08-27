\# Day 23–24 — Dataset Validation \& Preprocessing Verification Report



\*\*Project:\*\* HisabDo Web App AI  

\*\*Department:\*\* Department 1 – Capstone Development  

\*\*Track:\*\* AI/ML  

\*\*Workstream:\*\* AI Financial Assistant / Chatbot  

\*\*Intern:\*\* Rameesha Zafar  

\*\*Task:\*\* Validate input CSV/JSON dataset formats for missing values and incorrect data types, verify data preprocessing scripts to ensure clean data feeds into model pipelines  

\*\*Day:\*\* 23–24  



\---



\## 1. Objective



The objective of Day 23–24 is to ensure data integrity for the HisabDo AI Financial Assistant workstream by executing rigorous dataset validation and verifying data preprocessing pipelines.



This document serves to:

\* Validate transaction and budget datasets (CSV/JSON formats) for structural integrity, missing values, and incorrect data types.

\* Verify preprocessing transformation scripts to guarantee clean inputs for downstream RAG retrieval, vector search, and LLM query pipelines.

\* Provide an automated dataset verification script (`scripts/validate\_financial\_dataset.py`) to maintain ongoing data quality standards.



\---



\## 2. Dataset Schema Requirements



To ensure zero pipeline failures, incoming user financial transaction datasets must strictly conform to the following schema specification:



| Field Name | Type | Constraint | Description |

| :--- | :--- | :--- | :--- |

| `transaction\_id` | String / UUID | Required, Unique | Unique identifier for the expense transaction. |

| `user\_id` | String | Required | ID linking transaction to a specific user account. |

| `amount` | Float / Int | Required, Numerical > 0 | Expense value (must be numeric, no raw currency symbols). |

| `category` | String | Required | Normalized category label (e.g., `Groceries`, `Food`, `Rent`). |

| `date` | String (ISO 8601) | Required, `YYYY-MM-DD` | Timestamp of transaction for date-range filtering. |

| `description` | String | Optional | Natural language text describing the transaction. |



\---



\## 3. Data Validation \& Preprocessing Audit Matrix



| Verification Check | Target Dataset / Pipeline | Validation Criteria | Verification Method | Status | Audit Findings |

| :--- | :--- | :--- | :--- | :--- | :--- |

| \*\*VAL-01: Null Value Check\*\* | `data/sample\_transactions.json` | 0 null/missing values in required fields (`amount`, `category`, `date`). | Automated script `validate\_financial\_dataset.py` | \*\*PASSED (Script Verified)\*\* | 0 missing fields identified in baseline mock schema. |

| \*\*VAL-02: Type Consistency\*\* | `data/sample\_transactions.json` | Numerical fields must be `float`/`int`; dates must follow ISO 8601 format. | Type assertions \& type-checking script | \*\*PASSED (Script Verified)\*\* | Currency symbols (`$`, `PKR`) removed prior to numerical parsing. |

| \*\*VAL-03: Category Normalization\*\* | Preprocessing Script | Standardize informal category strings (e.g., `"food"` -> `"Food"`). | String cleaning \& title casing transform | \*\*PASSED (Rule Verified)\*\* | Lowercase and informal strings normalized cleanly. |

| \*\*VAL-04: Date Parsing Readiness\*\* | Date Range Filter Engine | Validate string parsing for explicit and relative dates (`"YYYY-MM-DD"`). | Python `datetime.isoformat` validation | \*\*PASSED (Rule Verified)\*\* | Invalid date strings flagged cleanly. |

| \*\*VAL-05: Duplicate Check\*\* | Transaction Ingestion | Detect duplicate `transaction\_id` entries. | Unique key set comparison | \*\*PASSED (Rule Verified)\*\* | Duplicate transaction keys flagged for removal. |



\---



\## 4. Preprocessing Script Verification Summary



The data preprocessing pipeline has been verified for RAG and Chatbot query readiness:



1\. \*\*Cleaning Layer:\*\* Strips extraneous white spaces, resolves non-standard encodings, and drops completely empty records.

2\. \*\*Type Casting:\*\* Enforces strict floating-point representation for financial calculations (`amount: float`).

3\. \*\*Data Formatting for RAG:\*\* Formats JSON elements into structured context text strings suitable for embedding generation:

&#x20;  > `"Transaction ID: TXN\_01 | Date: 2026-08-01 | Category: Groceries | Amount: $50.00 | Description: Supermarket"`



\---



\## 5. Summary \& GitHub Evidence



\* \*\*Branch Created:\*\* `feature/task23-24-data-validation-rameesha`

\* \*\*Validation Script Added:\*\* `scripts/validate\_financial\_dataset.py`

\* \*\*Documentation File Added:\*\* `docs/day23-24-dataset-validation-and-preprocessing-verification.md`

