\# Day 25 — Dataset Validation, Preprocessing Verification \& SQA Handover Report



\*\*Project:\*\* HisabDo Web App AI  

\*\*Department:\*\* Department 1 – Capstone Development  

\*\*Track:\*\* AI/ML  

\*\*Workstream:\*\* AI Financial Assistant / Chatbot  

\*\*Intern:\*\* Rameesha Zafar  

\*\*Task:\*\* Validate input CSV/JSON dataset formats for missing values, duplicate entries, and incorrect data types; verify automated preprocessing scripts for SQA handover  

\*\*Day:\*\* 25  



\---



\## 1. Objective



The objective of Day 25 is to execute final dataset validation, duplicate detection, and preprocessing verification as part of the Feature Stabilization \& SQA Handover phase for Department 1.



This document serves to:

\* Validate transaction and budget data schemas for missing fields, duplicate transaction IDs, and invalid data types.

\* Verify automated data cleaning scripts to guarantee zero pipeline failures during SQA testing and model evaluation.

\* Provide an updated verification script (`scripts/validate\_financial\_dataset\_day25.py`) supporting the SQA handover pipeline.



\---



\## 2. Dataset Schema \& Validation Constraints



Input financial datasets provided to the AI Financial Assistant and RAG retriever must pass the following SQA validation gates:



| Attribute Name | Data Type | Constraint | SQA Pass Criteria |

| :--- | :--- | :--- | :--- |

| `transaction\_id` | String / UUID | Required, Unique | Zero duplicate IDs allowed. |

| `user\_id` | String | Required | Must map to an active user session context. |

| `amount` | Float / Int | Numerical > 0 | No raw currency symbols or string numbers. |

| `category` | String | Standardized Label | Case-normalized (e.g., `Groceries`, `Utilities`). |

| `date` | ISO 8601 String | `YYYY-MM-DD` | Must pass valid date parsing checks. |

| `description` | String | Non-Null String | Natural language text for vector embedding generation. |



\---



\## 3. SQA Validation \& Preprocessing Execution Log



| Test Gate | Scope | Check Description | Verification Method | Status | SQA Audit Result |

| :--- | :--- | :--- | :--- | :--- | :--- |

| \*\*VAL-25-01\*\* | Data Integrity | Null / Missing value detection in mandatory JSON fields. | Script run `validate\_financial\_dataset\_day25.py` | \*\*PASSED\*\* | 0 null fields identified in baseline dataset. |

| \*\*VAL-25-02\*\* | Data Integrity | Unique key check for duplicate `transaction\_id` records. | Hash set unique key check | \*\*PASSED\*\* | 0 duplicate records found. |

| \*\*VAL-25-03\*\* | Type Check | Strict numerical type casting for transaction `amount`. | Python type assertions | \*\*PASSED\*\* | Floating-point conversion verified. |

| \*\*VAL-25-04\*\* | Preprocessing | String normalization \& whitespace stripping on `category`. | Regex \& string cleanup pipeline | \*\*PASSED\*\* | Categories normalized to title case. |

| \*\*VAL-25-05\*\* | RAG Feed | Formatting records for vector embeddings \& prompt injection. | Data transformer check | \*\*PASSED\*\* | JSON records converted into RAG text chunks. |



\---



\## 4. Preprocessing Script \& SQA Handover Verification



The dataset preprocessing pipeline has been verified for feature stabilization:



1\. \*\*Automated Validation Script:\*\* Added `scripts/validate\_financial\_dataset\_day25.py` to automate record filtering and duplicate removal.

2\. \*\*Clean Data Feed:\*\* Confirmed that preprocessed transaction payloads feed cleanly into downstream RAG vector indexes without schema errors.

3\. \*\*SQA Readiness:\*\* The dataset validation module is stabilized and ready for independent SQA execution.



\---



\## 5. Summary \& GitHub Evidence



\* \*\*Branch Created:\*\* `feature/task15-25-data-validation-rameesha`

\* \*\*Validation Script:\*\* `scripts/validate\_financial\_dataset\_day25.py`

\* \*\*Documentation File:\*\* `docs/day25-dataset-validation-and-sqa-handover.md`

