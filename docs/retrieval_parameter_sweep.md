# Retrieval Parameter Sweep

- Verified documents: 12
- Queries tested: 7 rewritten Day 1 queries.
- Method: existing verified-only TF-IDF cosine retrieval.
- Target labels: faq-001 for overview and faq-005 for PDF reporting.
- The other five questions have no confirmed exact workflow target in this evaluation.

| Threshold | top_k | Overview target | PDF target | Queries with results | Total passages |
|---:|---:|---|---|---:|---:|
| 0.12 | 1 | Yes | Yes | 7/7 | 7 |
| 0.12 | 2 | Yes | Yes | 7/7 | 13 |
| 0.12 | 3 | Yes | Yes | 7/7 | 18 |
| 0.20 | 1 | Yes | Yes | 7/7 | 7 |
| 0.20 | 2 | Yes | Yes | 7/7 | 12 |
| 0.20 | 3 | Yes | Yes | 7/7 | 15 |
| 0.30 | 1 | Yes | Yes | 6/7 | 6 |
| 0.30 | 2 | Yes | Yes | 6/7 | 9 |
| 0.30 | 3 | Yes | Yes | 6/7 | 10 |
| 0.40 | 1 | Yes | Yes | 6/7 | 6 |
| 0.40 | 2 | Yes | Yes | 6/7 | 7 |
| 0.40 | 3 | Yes | Yes | 6/7 | 7 |
| 0.50 | 1 | Yes | Yes | 4/7 | 4 |
| 0.50 | 2 | Yes | Yes | 4/7 | 4 |
| 0.50 | 3 | Yes | Yes | 4/7 | 4 |
| 0.60 | 1 | Yes | Yes | 3/7 | 3 |
| 0.60 | 2 | Yes | Yes | 3/7 | 3 |
| 0.60 | 3 | Yes | Yes | 3/7 | 3 |
| 0.70 | 1 | Yes | No | 1/7 | 1 |
| 0.70 | 2 | Yes | No | 1/7 | 1 |
| 0.70 | 3 | Yes | No | 1/7 | 1 |

## Query inspection at threshold 0.12, top_k=3

| Question | Returned documents and scores |
|---|---|
| Overview | faq-001 (What is HisabDo?, 0.7055); faq-khata-guidance (What is Khata and how is it used?, 0.4542); faq-005 (How do I export my expenses?, 0.3539) |
| Categorize expense | finance_003 (What is an expense?, 0.5713); faq-001 (What is HisabDo?, 0.2053) |
| Wrong prediction | finance_003 (What is an expense?, 0.6912) |
| PDF report | faq-005 (How do I export my expenses?, 0.6348); faq-001 (What is HisabDo?, 0.3308); faq-udhar-guidance (How can I understand Udhar or customer balances?, 0.1349) |
| Income and expense totals | faq-001 (What is HisabDo?, 0.4350); faq-khata-guidance (What is Khata and how is it used?, 0.3769); finance_002 (What is revenue?, 0.2294) |
| Add customer | faq-udhar-guidance (How can I understand Udhar or customer balances?, 0.2976); faq-001 (What is HisabDo?, 0.2726); faq-005 (How do I export my expenses?, 0.2541) |
| Record expense | finance_003 (What is an expense?, 0.4840); faq-001 (What is HisabDo?, 0.1739); faq-005 (How do I export my expenses?, 0.1453) |

## Interpretation and limitations

This sweep measures threshold and top_k effects on the existing verified-only TF-IDF retriever. The two target labels are limited to overview and PDF reporting. A returned result for the other five queries does not prove that it contains correct workflow instructions.

This test does not evaluate semantic embeddings, hybrid retrieval, metadata-filter ablations, or reranking. No production threshold is declared optimal from these results alone. The missing workflow documents must be written and verified before claiming all seven questions are answerable.
