# Department 3 Retrieval Strategy Comparison Matrix

Evaluation questions: 60; staged chunks: 12.
Verified questions used for hit-rate/MRR: 41.
Unverified questions excluded from positive relevance scoring: 19.

| Strategy | Hit rate @3 | MRR | Description |
|---|---:|---:|---|
| dense_vector | 95.12% | 0.9130 | Cosine similarity over pinned MiniLM embeddings. |
| bm25_lexical | 92.68% | 0.8260 | Pure-Python BM25 lexical retrieval. |
| hybrid_rrf | 95.12% | 0.8882 | Reciprocal Rank Fusion of dense and BM25 rankings. |
| hybrid_metadata | 82.93% | 0.7602 | Hybrid RRF with verified, intent-specific, fail-closed source eligibility. |
| hybrid_metadata_rerank | 85.37% | 0.7724 | Intent-filtered hybrid ranking with deterministic lexical reranking; experimental. |

## Top-k comparison

| Strategy | K | Hit rate | MRR |
|---|---:|---:|---:|
| dense_vector | 1 | 87.80% | 0.9130 |
| dense_vector | 3 | 95.12% | 0.9130 |
| dense_vector | 5 | 95.12% | 0.9130 |
| bm25_lexical | 1 | 70.73% | 0.8260 |
| bm25_lexical | 3 | 92.68% | 0.8260 |
| bm25_lexical | 5 | 100.00% | 0.8260 |
| hybrid_rrf | 1 | 80.49% | 0.8882 |
| hybrid_rrf | 3 | 95.12% | 0.8882 |
| hybrid_rrf | 5 | 97.56% | 0.8882 |
| hybrid_metadata | 1 | 68.29% | 0.7602 |
| hybrid_metadata | 3 | 82.93% | 0.7602 |
| hybrid_metadata | 5 | 82.93% | 0.7602 |
| hybrid_metadata_rerank | 1 | 70.73% | 0.7724 |
| hybrid_metadata_rerank | 3 | 85.37% | 0.7724 |
| hybrid_metadata_rerank | 5 | 85.37% | 0.7724 |

## Calibrated operating point

The threshold sweep favors dense-vector top-k=3 with a provisional threshold of 0.40: 33 TP, 1 FP, 6 FN, 97.1% precision and 84.6% recall across 41 verified questions, measured by expected-source hit. At threshold 0.50, precision reached 100% in this sample but recall fell to 61.5% (24 TP, 0 FP, 15 FN). Therefore 0.40 is the selected candidate for balanced retrieval; it is not a universal relevance guarantee. Verified-source eligibility, intent restrictions and safe abstention remain required. These are source-hit metrics, not passage-level answer-correctness metrics.
