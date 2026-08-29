\# Day 28 — Production Dataset Cleaning, Deployment Setup \& Pipeline Support Report



\*\*Project:\*\* HisabDo Web App AI  

\*\*Department:\*\* Department 1 – Capstone Development  

\*\*Track:\*\* AI/ML  

\*\*Workstream:\*\* AI Financial Assistant / Chatbot  

\*\*Intern:\*\* Rameesha Zafar  

\*\*Task:\*\* Run final validation and cleaning scripts across evaluation sample datasets to ensure zero missing or malformed inputs, configure deployment template, and maintain pipeline data coverage  

\*\*Day:\*\* 28  



\---



\## 1. Objective



The objective of Day 28 is to finalize production dataset sanitization, deploy runtime environment configuration templates, and support pre-evaluation QA readiness for Department 1.



This document details:

\* Final validation and cleaning across production transaction datasets to eliminate missing fields, duplicate IDs, and malformed inputs.

\* Creation of `.env.example` containing essential runtime configuration keys for production deployment.

\* Execution of an automated production cleaning utility script (`scripts/day28\_production\_dataset\_cleaning.py`) to feed clean data into model and RAG evaluation pipelines.



\---



\## 2. Production Dataset Sanitization Audit



| Audit Gate | Scope | Target Rule | Audit Result | Status |

| :--- | :--- | :--- | :--- | :--- |

| \*\*PROD-28-01\*\* | Data Deduplication | 0 duplicate `transaction\_id` records in output dataset. | 0 Duplicates detected | \*\*PASSED\*\* |

| \*\*PROD-28-02\*\* | Schema Completeness | 0 missing values in `amount`, `category`, `date`, or `user\_id`. | Missing fields filtered | \*\*PASSED\*\* |

| \*\*PROD-28-03\*\* | Numerical Integrity | Enforce positive float representation for transaction amounts. | Type conversion verified | \*\*PASSED\*\* |

| \*\*PROD-28-04\*\* | Text Normalization | Title-case category strings and trim whitespace on descriptions. | Category text normalized | \*\*PASSED\*\* |

| \*\*PROD-28-05\*\* | Production Asset | Export clean transaction asset to `data/cleaned\_production\_dataset\_day28.json`. | Production file exported | \*\*PASSED\*\* |



\---



\## 3. Deployment Setup \& Environment Variables



To comply with Day 28 pre-evaluation deployment setup guidelines, `.env.example` was created containing required runtime keys:



\* `PORT`, `NODE\_ENV`, `BASE\_URL` (Server network settings)

\* `MONGO\_URI`, `DB\_NAME` (Production database connection strings)

\* `LLM\_API\_KEY`, `MODEL\_NAME`, `VECTOR\_DB\_URL`, `EMBEDDING\_MODEL` (AI Inference \& RAG connectors)

\* `DATASET\_PATH`, `CONFIDENCE\_THRESHOLD` (Pipeline runtime variables)



\---



\## 4. Deliverables \& Repository Evidence



\* \*\*Branch Name:\*\* `feature/task28-data-validation-rameesha`

\* \*\*Deployment Template:\*\* `.env.example`

\* \*\*Cleaning Utility Script:\*\* `scripts/day28\_production\_dataset\_cleaning.py`

\* \*\*Documentation Report:\*\* `docs/day28-production-dataset-cleaning-and-pipeline-support.md`

