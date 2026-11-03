Careers Quality, Latency & Monitoring — updated 3 Nov 2026

OFFLINE RETRIEVAL BENCHMARK (10 queries, 976 indexed chunks):
Global TF-IDF: Hit Rate@5 80%; Precision@5 20%; MRR@5 0.583.
Careers metadata-filtered TF-IDF: Hit Rate@5 90%; Precision@5 26%; MRR@5 0.800.
These are local reproducible results, NOT live production retrieval metrics. Production embeddings and semantic reranker config were not in the supplied archive.

LIVE MANUAL REVIEW: 1 pass, 6 partial, 3 fail. Mean latency 1370 ms; median 1000 ms; nearest-rank p95 3000 ms. 0/10 technical errors reported (manual observations only).

See report, metrics CSV, ranked top-five details CSV, and benchmark script. Script requires scikit-learn and numpy and does not call production website/API.
