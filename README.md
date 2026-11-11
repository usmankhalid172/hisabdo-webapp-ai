# Department 4 Automated Retrieval Test Bench

Prepared for Muhammad Daniyal — Department 4.

## What is included

- `retrieval_test_bench.py` — dataset loader, domain-aware runner and CSV/JSON report writer.
- `retrieval_methods.py` — LSA vector proxy, BM25, RRF hybrid and reranking pipeline.
- `retrieval_metrics.py` — Recall@K, Precision@K, MRR, Hit Rate@K and macro aggregation.
- `test_retrieval_bench.py` — unit/regression tests.
- `domain_evaluation_dataset.jsonl` — consolidated source records, query records and relevance provenance from the uploaded archive.
- `per_query_results.csv` — 150 newly executed Blog query/configuration rows.
- `cross_domain_metrics.csv` and `cross_configuration_metrics.json` — new aggregate results and per-domain execution status.
- `reranker_config.yaml` — explicit benchmark settings.
- `AUTOMATED_RETRIEVAL_BENCHMARK_REPORT.md` — technical report and source inventory.
- `test_execution_log.txt` — exact commands and captured output.

## Requirements

Python 3.10+ recommended.

```bash
python -m pip install numpy scikit-learn pandas pyyaml pytest
```

`pandas` and `pyyaml` are needed only if you want to inspect/extend the original spreadsheet/YAML inputs; the benchmark runner itself requires NumPy and scikit-learn. `pytest` is required for tests.

## Run the benchmark

From this directory:

```bash
python retrieval_test_bench.py --dataset domain_evaluation_dataset.jsonl --out-dir .
```

The runner executes only a domain that has both:
1. a document corpus (`record_type=document`), and
2. labeled queries whose relevant document IDs match that corpus.

In the supplied archive, Blog & News is the only domain meeting both requirements. Other query records remain in the JSONL and are reported as `not_executed_missing_corpus` rather than being dropped or assigned invented scores.

## Run tests

```bash
python -m pytest -q
```

Tests use small synthetic documents for unit isolation. They do not replace the separate actual-data benchmark run.

## Retrieval configurations

| ID | Description |
|---|---|
| `vector_proxy` | TruncatedSVD/LSA over TF-IDF; a vector/latent-semantic proxy, not neural dense embeddings |
| `bm25` | Okapi BM25 |
| `hybrid_rrf` | Reciprocal Rank Fusion of LSA proxy and BM25 |
| `hybrid_rerank` | RRF candidate retrieval followed by lexical heuristic reranking |
| `reranked_topk` | RRF candidate pool (12 candidates), deduplication and heuristic final top-k |

RRF uses `k=60`; BM25 uses `k1=1.5`, `b=0.75`; default final K is 5 and candidate pool is 25. See `reranker_config.yaml`.

## Important model caveats

- No neural embedding model was available in the execution environment. The LSA method is explicitly marked as a proxy; it must not be represented as MiniLM or another neural dense model.
- The heuristic reranker is a transparent token/title overlap scoring fallback. It is not a cross-encoder.
- An optional cross-encoder code path exists when explicitly requested in code, but it was not executed and requires model/package availability and model download/cache.
- Existing historical metrics from the submissions are not mixed with the newly executed metrics.

## Dataset record types

The JSONL contains:
- `document` records: actual Blog articles and their stable IDs/source URLs.
- `query` records: domain, query ID, question, relevance judgment and label provenance.
- `execution_status`: `executable` or an explicit missing-corpus status.

Label types vary. Blog records use explicit article IDs. Career records preserve target chunk text rather than inventing IDs. Contact records preserve expected chunk references. HisabDo records preserve proxy expected paths. The latter three cannot be evaluated against the supplied archive because their document corpora are absent.

## Output metrics

- Recall@1/3/5
- Precision@1/3/5 (fixed K denominator)
- MRR
- Hit Rate@1/3/5
- Latency per query/configuration
- Ranked document IDs, scores, reranker tag and source URL provenance

## Integration notes

Before production integration:
1. Supply reviewed chunk corpora for every domain.
2. Convert target text/path labels into stable document IDs with source provenance.
3. Pin the intended embedding model and record model ID/vector dimensions.
4. Run neural dense retrieval and a real cross-encoder on the same held-out labels.
5. Keep heuristic reranking opt-in until recall regression is resolved.

See `AUTOMATED_RETRIEVAL_BENCHMARK_REPORT.md` for the full inventory, metrics, failures and limitations.
