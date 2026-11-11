# Automated Retrieval Test Bench & Reranker Pipeline

**Prepared by:** Muhammad Daniyal — Department 4  
**Input archive:** `blog-kb-cleaned.zip`  
**Benchmark execution date:** 11 November 2026  
**Status:** Partial cross-domain execution; Blog corpus executed, other domains retained but blocked by missing corpora.

## 1. Executive summary

The uploaded archive was fully extracted, including three nested ZIP archives and a DOCX file. It contains material for Blog & News, Careers & Job Openings, Contact & Locations, Portfolio & Tech Radar, HisabDo, and a nine-domain Department 4 configuration sign-off matrix.

The archive supplied a usable corpus only for Blog & News: 47 cleaned articles and 30 explicit gold-labeled queries in the existing benchmark script. The other domains supplied query records, target references, historical aggregate results, or configuration notes, but not the matching chunk corpora needed for a fair new retrieval run. Those domains are included in the consolidated dataset and explicitly marked as not executable; they were not silently omitted.

**Actual new execution:** 30 Blog queries × 5 configurations = 150 query/configuration runs. All 150 completed without retrieval errors. The 9 automated tests passed.

**Best measured configuration on the executable Blog slice:** Hybrid RRF using an LSA vector proxy plus BM25, with MRR 0.8067 and Recall@5 0.8333. This is only a small improvement over the LSA proxy alone (MRR 0.7972); the query-level hit rate at 5 remained 0.9333.

**Reranking conclusion:** The lexical heuristic reranker improved Precision@1 from 0.7000 to 0.7333, but reduced Recall@5 from 0.8333 to 0.8000 and Hit Rate@5 from 0.9333 to 0.8667. It is not an overall improvement and is not a cross-encoder.

## 2. Archive inspection and domain inventory

### 2.1 Extracted source inventory

| Source submission | Extracted contents | Evaluation evidence |
|---|---|---|
| `blog-kb-cleaned/` | Consolidated Markdown KB, Python benchmark, CSV logs, JSON summary, YAML threshold settings, report | 47 article documents; 30 gold-labeled positive queries; historical per-query and aggregate results |
| Careers ZIP | `Career_Hybrid_Retrieval_Evaluation.xlsx`, `Career_Filter_Audit_Log.docx` | 28 query rows extracted from workbook; target chunk text and configuration ranks; audit document states 31 audited queries |
| Contact & Locations ZIP | JSON evaluation log, CSV, XLSX, Markdown and DOCX sign-off | 8 Day 1 queries with expected chunk references/source URLs |
| Portfolio Day 1 Markdown | Historical evaluation report | Reports a 12-query benchmark and aggregate metrics; raw query list, relevance labels and corpus absent from this archive |
| HisabDo ZIP | Query log, calibration CSV, Python evaluator, Markdown report | 6 reconstructed proxy queries with expected source paths; no index/chunk corpus included |
| Corporate retrieval tuning DOCX | Query normalization and domain sign-off material | Nine-domain configuration matrix and recommendations; not a nine-domain corpus or complete set of relevance judgments |

### 2.2 Department 4 domain matrix

The corporate sign-off document lists these nine knowledge domains:

| Domain ID | Domain | Evaluation material in archive | New execution |
|---|---|---|---|
| DOM-01 | Contact Us & Locations | 8 queries, target chunk IDs/source URLs | Blocked: corpus absent |
| DOM-02 | Company Overview & Founder | Threshold/configuration notes | Blocked: questions and corpus absent |
| DOM-03 | Core Software Services | Threshold/configuration notes | Blocked: questions and corpus absent |
| DOM-04 | Strategic Architectural Pillars | Threshold/configuration notes | Blocked: questions and corpus absent |
| DOM-05 | Careers & Internship Academy | 28 workbook query rows; filter audit; target chunk text | Blocked: corpus absent |
| DOM-06 | Portfolio & Tech Radar | Historical 12-query aggregate report | Blocked: raw query labels and corpus absent |
| DOM-07 | Legal, Compliance & Privacy | Threshold/configuration notes | Blocked: questions and corpus absent |
| DOM-08 | Corporate Homepage & Brand Identity | Threshold/configuration notes | Blocked: questions and corpus absent |
| DOM-09 | Engineering Blog & Technical Guides | 47 articles and 30 explicit gold-labeled queries | Executed |

HisabDo is a separate product knowledge source represented in the archive. Its six evaluation queries are proxies reconstructed by its submitted evaluator/report, not verbatim Day 1 prompts. Its 976-chunk index and vectors are not included.

### 2.3 Evaluation data counts and caveats

| Domain | Corpus documents | Query records in consolidated JSONL | Label status |
|---|---:|---:|---|
| Blog & News | 47 | 30 | Explicit gold article IDs |
| Careers & Job Openings | 0 | 28 | Target chunk text in workbook; query wording reconstructed/authored |
| Contact & Locations | 0 | 8 | Expected chunk references and source URLs |
| HisabDo | 0 | 6 | Proxy questions and expected source paths |
| Portfolio & Tech Radar | 0 | 0 | Historical report states 12 queries, but raw query records not supplied |
| Company Overview & Founder | 0 | 0 | Configuration only |
| Core Software Services | 0 | 0 | Configuration only |
| Strategic Architectural Pillars | 0 | 0 | Configuration only |
| Legal, Compliance & Privacy | 0 | 0 | Configuration only |
| Corporate Homepage & Brand Identity | 0 | 0 | Configuration only |
| **Total in consolidated dataset** | **47** | **72** | Mixed label provenance; see each record |

**Career discrepancy:** the workbook's query-results sheet yields 28 rows with query IDs, while the accompanying audit document says 31 queries were audited (10 Day 1, 18 paraphrases, 3 controls). The 3-record discrepancy is not filled by invention.

**Portfolio omission:** the portfolio report refers to `portfolio-domain-failure-log-2026-11-05.md` and other source files that are not present in the uploaded archive. No portfolio query strings or labels were fabricated to fill this gap.

## 3. Retrieval architecture

### 3.1 Implemented configurations

1. **Vector proxy:** TruncatedSVD/LSA over TF-IDF vectors. This is a lightweight latent-semantic proxy, not a neural dense embedding.
2. **BM25:** Okapi BM25 with `k1=1.5`, `b=0.75`.
3. **Hybrid RRF:** reciprocal-rank fusion of LSA proxy and BM25 rankings, `rrf_k=60`.
4. **Hybrid + reranker:** RRF candidate pool followed by a transparent lexical-overlap heuristic.
5. **Reranked top-k:** same candidate generation and heuristic reranking, returning the final top 5 from a smaller 12-document candidate pool (versus 25 for the hybrid-rerank configuration).

The runner retains document IDs, source URLs, rank, scores, provenance/reranker label and latency for every returned result.

### 3.2 Dense retrieval and cross-encoder availability

The environment did not have `sentence-transformers` installed, and no neural embedding model was available locally. The benchmark therefore did **not** claim a true dense embedding run. The Blog source script's optional MiniLM branch was unavailable in this environment; its historical summary says `minilm`, but that historical metadata is not used as proof of current execution.

The reranker fallback is a lexical heuristic using query/document token overlap, title overlap and the RRF score. It is labelled `heuristic_fallback`, not a cross-encoder. The code contains an explicitly opt-in cross-encoder path, but it was not run.

### 3.3 Fairness

All five configurations use the same 47 Blog documents, same 30 queries, same gold article IDs and fixed K values (1, 3, 5). Metrics are macro-averaged per query. Precision@K uses fixed K as denominator, including when fewer than K results are returned.

No other domain was included in the numerical comparison because the corresponding source corpus was missing. Historical scores are described separately and never mixed into the newly executed results.

## 4. Metric definitions

- **Recall@K:** number of relevant retrieved documents in top K divided by the total number of known relevant documents for that query.
- **Precision@K:** number of relevant retrieved documents in top K divided by K.
- **MRR:** reciprocal rank of the first relevant result, averaged over queries.
- **Hit Rate@K:** fraction of queries with at least one relevant result in top K.
- **Latency:** elapsed retrieval time per query/configuration in milliseconds, measured locally; it excludes model download/startup and is not a production latency benchmark.

## 5. Newly executed results

### 5.1 Blog & News comparison

| Configuration | Recall@1 | Recall@3 | Recall@5 | Precision@1 | Precision@3 | Precision@5 | MRR | Hit Rate@5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LSA vector proxy | 0.4389 | 0.7278 | 0.8333 | 0.7000 | 0.4444 | 0.3067 | 0.7972 | 0.9333 |
| BM25 | 0.4444 | 0.7222 | 0.8167 | 0.7000 | 0.4444 | 0.3000 | 0.7900 | 0.9333 |
| Hybrid RRF | 0.4389 | 0.7278 | 0.8333 | 0.7000 | 0.4444 | 0.3067 | **0.8067** | 0.9333 |
| Hybrid + heuristic reranker | 0.4389 | 0.6889 | 0.8000 | **0.7333** | 0.4333 | 0.3000 | 0.7844 | 0.8667 |
| Reranked top-k | 0.4389 | 0.6889 | 0.8167 | **0.7333** | 0.4333 | 0.3067 | 0.7911 | 0.9000 |

### 5.2 Latency observations

| Configuration | Mean latency (ms/query) | Median latency (ms/query) |
|---|---:|---:|
| LSA vector proxy | 0.685 | 0.640 |
| BM25 | 0.647 | 0.618 |
| Hybrid RRF | 1.813 | 0.667 |
| Hybrid + heuristic reranker (25 candidates) | 10.080 | 8.986 |
| Reranked top-k (12 candidates) | 4.729 | 4.611 |

These are local offline measurements on a 47-document corpus. They should not be compared directly with production API or end-to-end response latency.

### 5.3 Per-query observations

- One query, `P6` (“how to build a chatobt for my website”), failed to retrieve any labeled relevant article in the top 5 under all five configurations.
- The heuristic reranker changed the top-1 result to a relevant document for `F1` and `H2`, but changed a relevant top-1 result to an irrelevant one for `F4`.
- Hybrid RRF and the LSA proxy had identical top-1 correctness on this run. Hybrid's MRR improvement was marginal (+0.0094).
- BM25 and Hybrid RRF each had 21/30 top-1 correct queries. The reranker had 22/30.

### 5.4 Reranking decision

The reranker should remain an experimental option, not the default production path. Both reranked variants gained +0.0333 Precision@1 over hybrid RRF. The 25-candidate hybrid reranker reduced Recall@5 by 0.0333 and Hit Rate@5 by 0.0667; the 12-candidate reranked top-k reduced Recall@5 by 0.0167 and Hit Rate@5 by 0.0333. Both had lower MRR than hybrid RRF. This is a precision/recall trade-off, not a measured overall improvement.

## 6. Cross-domain results and unavailable runs

Only Blog & News was executable as a fresh apples-to-apples retrieval benchmark. The consolidated evaluation dataset preserves the other domains' query records and label provenance.

| Domain | Status | Reason |
|---|---|---|
| Blog & News | Executed | Corpus and explicit gold IDs available |
| Careers & Job Openings | Not executed | No career chunks/documents in archive; target labels are target text, not corpus IDs |
| Contact & Locations | Not executed | No contact chunks/documents; expected chunk IDs alone cannot be searched |
| HisabDo | Not executed | No index/chunks/vectors; report's 976-chunk index is referenced but not attached |
| Portfolio & Tech Radar | Not executed | Only aggregate historical report; raw query-level benchmark and corpus absent |
| Company Overview & Founder | Not executed | Configuration notes only |
| Core Software Services | Not executed | Configuration notes only |
| Strategic Architectural Pillars | Not executed | Configuration notes only |
| Legal, Compliance & Privacy | Not executed | Configuration notes only |
| Corporate Homepage & Brand Identity | Not executed | Configuration notes only |

The overall metrics in `cross_domain_metrics.csv` are labelled `OVERALL_EXECUTED`. Since the only executable domain is Blog, these values are the Blog macro-averages, not a claim of nine-domain coverage.

## 7. Historical evidence kept separate

- **Contact & Locations:** the submission reports 8 Day 1 cases and tuned semantic/lexical scores, but no chunk corpus is supplied. Its claimed 100% context precision is a historical submission claim, not a result reproduced by this bench.
- **Careers:** the workbook includes historical S0–S7 target ranks and a filter audit. The workbook describes query wording as reconstructed/authored. Those historical rank results are not recalculated by this runner.
- **HisabDo:** its report describes six proxy questions and a 976 × 2,109 TF-IDF index, while metadata labels a sentence-transformer model. The actual index and fitted vectorizer are absent. Historical calibration numbers are not treated as new runs.
- **Portfolio:** the report describes 12 historical queries and lexical/term-vector experiments; it explicitly states the production chunk index was empty. Its aggregate metrics are not merged into this run.
- **Corporate tuning:** the DOCX lists thresholds and sign-off assertions for nine domains. It does not provide a shared nine-domain corpus or reproducible per-query data.

## 8. Automated test execution

Command:

```bash
python -m pytest -q
```

Actual result:

```text
.........                                                                [100%]
9 passed in 1.00s
```

The nine tests cover JSONL loading, malformed records, vector proxy retrieval, BM25 retrieval, RRF fusion, duplicate handling, heuristic reranking/provenance, recall/precision/MRR, empty results/missing labels, cross-domain skipping, report creation and reranked top-k.

The unit tests use small synthetic documents for isolated components. These are mocked/unit tests and are not counted as retrieval benchmark data. The 150 Blog query/configuration runs above are the separate actual-data execution.

## 9. Limitations and risks

1. No true neural dense embedding model or cross-encoder was loaded.
2. Only one of the nine corporate domains supplied an executable corpus.
3. Some domains have proxy or reconstructed queries, and Career target labels are not document IDs.
4. Blog query set combines previously failed, evaluation and held-out questions; the original script does not provide a reliable per-query Day 1 failure flag for all 30.
5. Relevance labels are inherited from the supplied Blog script, not newly human-judged.
6. A 47-document corpus is too small to establish production generalization.
7. The heuristic reranker is not a learned relevance model.
8. No answer-generation quality, citation entailment, web crawling, or deployed service latency was measured.
9. The source submissions include provenance inconsistencies and missing artifacts; see the domain inventory.

## 10. Production integration recommendations

1. Obtain the missing source corpora/chunk JSONL and original Day 1 query files for each domain.
2. Add stable chunk IDs, canonical source URLs, domain IDs and human-reviewed relevance judgments to one common evaluation format.
3. Rebuild the HisabDo vector index and metadata together; its submitted report warns that metadata claims MiniLM while the actual vectors are TF-IDF.
4. Rebuild Portfolio's application index from approved current sources before using the historical FAQ corpus for answer generation.
5. Install and pin a specific neural embedding model, record its exact model ID/version and vector dimension, and benchmark it against BM25/RRF on the same labels.
6. Add a real cross-encoder reranker only after measuring its latency and retrieval quality on held-out judgments.
7. Keep the heuristic reranker disabled by default until its recall regression is addressed.
8. Add domain-specific release gates: minimum Recall@5, MRR, cross-domain leakage rate and citation/source correctness, reviewed by a human.
9. Re-run this bench after each corpus/index/model change and store the run configuration with every result.

## 11. Reproducibility

See `README.md` for installation, commands, configuration, expected outputs and limitations. The detailed per-query evidence is in `per_query_results.csv`; aggregate results are in `cross_domain_metrics.csv` and `cross_configuration_metrics.json`.

**Final verdict:** the submission provides a genuinely executed and tested Blog retrieval bench, a reusable multi-method pipeline, and an honest cross-domain inventory. It does not claim a complete nine-domain benchmark because the uploaded ZIP does not contain the corpora required to execute those domains.
