# Department 3 Chunking and Embedding Configuration Decisions

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-10 · **Branch:** `FahadZubairi_AI`
**Experiment:** `scripts/chunking_experiment.py` → `data/retrieval_eval/results/chunking_experiment.json`
**Manifest:** `data/kb/dept3/index_manifest.json` (written by every ingestion run)

## 1. Content profile (363 records)

| Content type | Records | Median chars | Max chars | Shape |
|---|---|---|---|---|
| Structured FAQ (Help Center, blog FAQs) | 110 | 257 | 666 | One question, one short self-contained answer |
| Product documentation (features, about, platform) | 34 | 216 | 666 | Short feature sections |
| Workflow guidelines (finance guides, how-tos) | 180 | 458 | 1327 | Step lists and multi-paragraph explanations |
| Long-form user documentation (privacy, terms) | 40 | 386 | 1067 | Numbered legal sections, reference only |
| Accounting feature tables | 0 | | | No approved page has a table today; rule below applies when one appears |

## 2. Experiment

Five chunking configurations were tested on the 58 answerable judged questions (development and held-out sets). The
retriever was the production hybrid: bge-small plus BM25, alpha 0.6, top 2. The table shows the share of questions
where at least half of the judged answer reached the top-2 context.

| Config | Pieces | Max chars | Answer hit rate | FAQ | Product doc | Workflow | Noise share | Context chars / question |
|---|---|---|---|---|---|---|---|---|
| **current** (≤1500, no overlap) | 364 | 1327 | **0.741** | 24/30 | 10/14 | 9/14 | 0.110 | **667** |
| s800 (≤800) | 374 | 798 | 0.741 | 24/30 | 10/14 | 9/14 | 0.110 | 664 |
| s800_ov (≤800 + 1 paragraph overlap) | 374 | 942 | 0.759 | 24/30 | 10/14 | 10/14 | 0.096 | 679 |
| s500_ov (≤500 + overlap) | 467 | 942 | 0.759 | 24/30 | 10/14 | 10/14 | 0.105 | 650 |
| merge2000 (sections merged to 2000) | 186 | 2264 | 0.759 | 23/30 | 9/14 | 12/14 | 0.073 | 1598 |

What it shows:

* **FAQs:** splitting never applies (max 666 chars). Merging FAQs with nearby sections loses one FAQ hit, so FAQs stay
  one question per record.
* **Product docs:** every option is equal or worse than the current setting.
* **Workflow guides:** these are the only type that benefits. Merging gains 3 of 14 but sends 2.4× the context and
  loses FAQ and product hits. Overlap gains 1 of 14 (one question), which is within noise for 58 questions.
* **Splitting smaller** (800, 500) changes nothing without overlap, because only 10 sections exceed 800 characters.

## 3. Decisions

| Content type | Chunk unit | Max size | Overlap | Reason |
|---|---|---|---|---|
| Structured FAQ | One question + its full answer | Never split | None | Answers are short and complete; splitting would separate the question from its answer |
| Product documentation | One section (h2/h3) | 1500 chars | None | No option measured better |
| Workflow guidelines | One section; split at sub-headings, then paragraphs | 1500 chars | None (kept) | Overlap gain is one question, inside noise; changing it would force a threshold recalibration. **Re-test with s800_ov when the workflow question set reaches 30+ questions** |
| Long-form documentation (legal) | One numbered section | 1500 chars | None | Reference only: quoted and linked, never paraphrased, so exact section boundaries matter more than recall |
| Accounting feature tables | Whole table if ≤1500 chars; else split by rows with the header row repeated in every piece | 1500 chars | Header row | A row without its header is meaningless; rows are never cut |
| Short intros (<150 chars) | Merged into the next section | | | A one-line intro alone has no answer |

The production configuration is **unchanged**. This is a measured decision, not a default.

## 4. Embedding and index parameters (reproducibility)

All values are recorded automatically in `index_manifest.json` by every ingestion run. A build is reproducible when the
model file hash, versions and parameters below match.

| Item | Value |
|---|---|
| Embedding model | `BAAI/bge-small-en-v1.5` |
| Model file actually loaded | `qdrant/bge-small-en-v1.5-onnx-q`, snapshot `aa8f8b060edb00e03bfdd08813a2949946c8ba55`, `model_optimized.onnx` (quantized ONNX) |
| Model file SHA-256 | `51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431` |
| Dimensions, normalisation, similarity | 384 · L2 · cosine (dot product of unit vectors) |
| Query prefix | `Represent this sentence for searching relevant passages: ` |
| Passage text | `"{title}. {heading}.\n{body}"` |
| Vector checksum (363 records) | `e5e0cb7482e12318` (SHA-256 of vectors rounded to 5 decimals) |
| BM25 | k1 1.5 · b 0.75 · score saturation `s/(s+5)` · tokenizer `[a-z0-9]+` and Urdu letters, stop words removed |
| Hybrid | 0.6 × cosine + 0.4 × BM25 · threshold 0.566273 · top_k 2 · margin 0.05 · 20 candidates |
| Lexical fallback (no fastembed) | threshold 3.857 · top_k 2 · margin 2.0 |
| Index | In-memory exact search (NumPy matrix, no ANN index). No HNSW or IVF parameters, so results are exact and deterministic |
| Environment | Python 3.13.0 · fastembed 0.7.3 · onnxruntime 1.31.1 · numpy 2.4.4 · tokenizers 0.23.3 · beautifulsoup4 4.15.0 |
| KB version | `9822a06e49cc` (hash of record content hashes) |

Rules:

1. **Pin the versions** above in the build environment. fastembed may later resolve the same model name to a different
   file. If `onnx_sha256` in a new manifest differs, the vectors are different: rerun the retrieval and grounded-answer
   evaluations and recalibrate the threshold before release.
2. **Model cache:** set `FASTEMBED_CACHE_PATH` to a fixed folder in CI so the same file is reused (the default is the
   temp folder, which can be cleared).
3. **Changing the chunking or the model** requires a new manifest, a retrieval evaluation and recalibration
   (`docs/dept3-monitoring-runbook.md` §5.3).
