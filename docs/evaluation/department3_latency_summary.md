# Department 3 Local Retrieval Latency Benchmark

- Scope: local FAQ retrieval only; excludes full chatbot and external API latency.
- Dataset: verified questions from department3_evaluation_set_v1.0.csv.
- Runs: one measured retrieval per verified question; one warm-up excluded.
- Embeddings: configured local FAQ embedding model.

## Results

- Verified questions measured: 41
- Retrieval success: 35
- Empty retrievals: 6
- Average latency: 18.47 ms
- Median latency (p50): 18.47 ms
- p95 latency: 21.07 ms
- Maximum latency: 21.37 ms
- Questions with at least one expected source matched: 30/41

## Limitations

- This is a local single-run-per-question measurement, not a load test.
- Source match is not answer accuracy.
- External provider/API latency and monetary cost were not measured.
- Results depend on the local machine and current runtime conditions.
