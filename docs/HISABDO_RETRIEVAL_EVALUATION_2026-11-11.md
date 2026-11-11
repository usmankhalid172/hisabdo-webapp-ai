# HisabDo Feature Retrieval Evaluation

**Evaluation date:** 11 November 2026  
**Scope:** HisabDo product and feature references in the checked-in XICTEK website assistant index  
**Purpose:** Compare unrestricted cosine retrieval with a product-page metadata filter and calibrate top-k and score thresholds.

## Executive summary

On six reconstructed query proxies based on Day 1 cases FV-01 through FV-06, filtering retrieval to canonical HisabDo product/help pages improved the controlled top-5, 0.12-threshold comparison from **5/6 query hits and 0.314 mean unique-source precision** to **6/6 hits and 0.689 precision**. The baseline's low precision came from mixing product queries with unrelated portfolio, company, career, profile, and HisabDo blog sources.

For this small evaluation set, the best measured filtered setting was **top_k=3 and cosine threshold=0.10**: 6/6 query hits, 0.806 mean unique-source precision, and no empty retrievals. This is a **provisional calibration**, not a production guarantee. The index uses TF-IDF lexical vectors, not a sentence-transformer semantic embedding, and the original Day 1 prompt strings were not included in the repository.

## Day 1 case basis

The source was `docs/Department4_Master_Handover_2026-11-04/member_submissions/HisabDo_Product_Module_Final_Validation_Report.docx`. It records FV-01 to FV-06 as one fail, three partial, and two pass. It describes the tested intents and outcomes, but does not include the verbatim prompts. The queries in the generated log are therefore **representative proxies reconstructed from the recorded case descriptions**, not claimed copies of the original prompts.

| Case | Day 1 status | Evaluation query proxy | Expected supporting page paths |
|---|---|---|---|
| FV-01 | Fail | What is HisabDo and what business problem does it solve? | `/`, `/about`, `/about-app`, `/app`, `/faq` |
| FV-02 | Pass | Can I use HisabDo without creating an account? | `/`, `/about`, `/about-app`, `/app`, `/faq` |
| FV-03 | Partial | Which HisabDo features can I use offline without internet? | `/`, `/about`, `/about-app`, `/app`, `/faq` |
| FV-04 | Partial | When I sign in, are my existing local records uploaded, merged, or replaced? | `/faq`, `/privacy-policy` |
| FV-05 | Pass | Can I manage customer balances and see each customer's transaction history? | `/about`, `/about-app`, `/app`, `/faq` |
| FV-06 | Partial | What information is included in HisabDo PDF reports or statements? | `/about`, `/about-app`, `/app`, `/faq` |

## Methods

### Baseline: unrestricted current cosine retrieval

- Ranked all **976** indexed chunks using the existing query vector and cosine dot product.
- Applied each tested score threshold and top-k limit.
- Used the current query-time TF-IDF transform and synonym expansion from `src/xictek_website_assistant/embeddings.py`.

### Metadata-assisted hybrid: canonical product-page filter plus the same vector ranking

- Applied source metadata before ranking: `host=hisabdo.app` and a canonical product/help path in `/`, `/about`, `/about-app`, `/app`, `/faq`, or `/privacy-policy`.
- This retained **82 of 976 chunks** for candidate search and excluded blog, career, founder/profile, and unrelated XICTEK pages.
- Applied the same cosine scores, thresholds, and top-k options as the baseline. No different embedding or generation model was used.

### Important representation note

The active implementation in `embeddings.py` uses `TfidfVectorizer`; its vectors are lexical TF-IDF values stored as dense NumPy arrays. That is not a neural dense semantic embedding. The checked-in `metadata.json` labels the index as `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, while the vector matrix is **976 × 2,109** and the repository code uses a fitted TF-IDF vectorizer. The sklearn pickle also emitted a version warning: it was created with 1.5.2 and evaluated with 1.7.2. Therefore, this is a comparison of the **current cosine/TF-IDF baseline versus metadata-filtered cosine/TF-IDF**, not a validated semantic-dense-versus-hybrid experiment. Correct the index provenance and rerun with a pinned sklearn version before treating scores as release evidence.

## Results

| Comparison | Top-k | Threshold | Query hits | Mean unique-source precision | Mean expected-source coverage | Empty results |
|---|---:|---:|---:|---:|---:|---:|
| Unrestricted baseline, controlled | 5 | 0.12 | 5/6 (83.3%) | 0.314 | 0.342 | 0 |
| Metadata-filtered, controlled | 5 | 0.12 | 6/6 (100%) | 0.689 | 0.533 | 0 |
| Unrestricted baseline, best measured calibration | 8 | 0.12 | 6/6 (100%) | 0.278 | 0.492 | 0 |
| Metadata-filtered, best measured calibration | 3 | 0.10 | 6/6 (100%) | 0.806 | 0.492 | 0 |

Unique-source precision is calculated over distinct returned source pages, not claim-level entailment. The log also retains exact returned paths, titles, and scores for review. Query-hit means that at least one page path listed as expected for that proxy appeared in the retrieved results; it does not mean that every requested detail is documented.

### Case observations

- **FV-01:** The unrestricted top eight included portfolio, company/about, founder, company blog, and services references before the HisabDo landing page. The filtered top three were HisabDo home, app, and app-overview pages. This matches the Day 1 failure type: a broad product question can be displaced by unrelated company material.
- **FV-02:** The filtered set returned FAQ/privacy sources; guest mode is present in the FAQ. The relevant source page should still be checked before generation to avoid answering from privacy text that does not address the whole question.
- **FV-03:** The FAQ and overview are retrieved. The benchmark records source-page retrieval only; feature-by-feature offline availability must be grounded in the returned text.
- **FV-04:** The FAQ is retrieved, but neither metadata filtering nor a lower threshold can supply undocumented local-record migration behavior. The returned public material describes supported synchronization; it does not resolve whether local records upload, merge, or are replaced. Keep that answer explicitly uncertain until product documentation confirms it.
- **FV-05 / FV-06:** FAQ, app, and overview pages appear in filtered results. Retrieval does not independently verify PDF field completeness or the current mobile-app implementation.

## Threshold calibration

The accompanying CSV evaluates thresholds **0.00, 0.05, 0.10, 0.12, 0.15, 0.20, 0.25, and 0.30** at top-k **3, 5, and 8** for both methods. At metadata-filtered top-k 3, thresholds 0.10 and 0.12 both returned a supporting page for all six cases. Threshold 0.10 had higher mean expected-source coverage (0.492 vs. 0.425); at 0.15 the hit rate fell to 5/6. This supports **0.10 as a provisional HisabDo product-page setting for the checked-in index**, pending a held-out benchmark and consistent index provenance.

## Deliverables and reproduction

- Query-level retrieval log: `docs/HISABDO_RETRIEVAL_QUERY_LOG_2026-11-11.csv`
- Top-k and threshold grid: `docs/HISABDO_RETRIEVAL_THRESHOLD_CALIBRATION_2026-11-11.csv`
- Reproducible evaluator: `scripts/evaluate_hisabdo_retrieval.py`

From the repository root, run:

```powershell
python scripts/evaluate_hisabdo_retrieval.py
```

The environment must include the repository requirements and the index/vectorizer files. The script validates the vector/chunk count and query-vector dimension before scoring.

## Limits and next steps

1. Obtain the exact FV-01 through FV-06 query strings and rerun them; retain the current proxies only as provisional examples.
2. Rebuild index metadata so it accurately identifies TF-IDF, or rebuild vectors using the intended dense model and compare again. Do not mix TF-IDF vectors with sentence-transformer queries.
3. Pin scikit-learn to the index build version, or rebuild the vectorizer and vectors together in the target environment.
4. Add held-out paraphrases and feature-combination queries before choosing a production threshold.
5. Keep FV-04's merge/replacement behavior as an evidence gap; retrieval tuning cannot substitute for an approved product specification.
6. No live website crawl, deployed index check, generated-answer evaluation, or production configuration change was performed.
