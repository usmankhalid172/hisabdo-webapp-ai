
# HisabDo Advanced Retrieval - Evaluation Report

## 1. Objective

The purpose of this evaluation was to improve FAQ retrieval by implementing semantic, lexical, and hybrid search, query normalization, metadata filtering, reranking, and unrelated-query rejection.

## 2. Evaluation Dataset

The evaluation dataset contains six test questions:

- Receivable definition
- Supplier payable question
- Cash flow explanation
- Customer payment workflow
- Roman Urdu customer balance question
- Unrelated Mars weather question

Expected relevant FAQ IDs were defined for each question.

Only verified FAQ documents were included in retrieval.

## 3. Retrieval Methods

### Semantic Retrieval
Uses multilingual sentence embeddings to calculate similarity between the user query and every verified FAQ document.

### Lexical Retrieval
Uses BM25-style term matching to identify documents containing relevant query terms.

### Hybrid Retrieval
Combines semantic and lexical scores using equal weights:

- Semantic weight: 50%
- Lexical weight: 50%

### Additional Improvements
- English and Roman Urdu query normalization
- Stopword removal and word mapping
- Metadata-based product area filtering
- Lightweight reranking using title and question overlap
- Top-K result selection
- Threshold-based filtering
- Unrelated-question rejection

## 4. Evaluation Metrics

The following metrics were used:

- Precision@3: Relevant retrieved results divided by 3.
- Recall@3: Relevant retrieved results divided by total relevant documents.
- MRR: Reciprocal rank of the first relevant result.
- nDCG@3: Ranking quality based on the positions of relevant results.
- Unrelated false returns: Number of unrelated queries that returned results.

## 5. Performance Comparison

| Metric | Semantic | Lexical | Hybrid |
|---|---:|---:|---:|
| Precision@3 | 0.2778 | 0.2778 | 0.2778 |
| Recall@3 | 0.8333 | 0.8333 | 0.8333 |
| MRR | 0.8333 | 0.8333 | 0.8333 |
| nDCG@3 | 0.8333 | 0.8333 | 0.8333 |
| Unrelated false returns | 0 | 0 | 0 |

## 6. Key Findings

- All five relevant test questions retrieved their expected FAQ at rank 1 for all three methods.
- The supplier-related question improved after query normalization.
- The Roman Urdu customer balance question retrieved faq-006.
- The unrelated Mars weather question returned no results.
- All three retrieval methods achieved identical aggregate metrics on this dataset.

## 7. Selected Configuration

The hybrid method is retained as the combined retrieval option because it uses both semantic meaning and lexical matching.

Current configuration:

- Default Top-K: 3
- Default threshold: 0.15
- Semantic threshold: 0.45
- Unrelated semantic threshold: 0.55
- Semantic weight: 0.50
- Lexical weight: 0.50
- Reranking weight: 0.80
- Title/question overlap weight: 0.20

These settings are initial evaluation settings, not universally optimized values. A larger and more diverse dataset is required for further tuning.

## 8. Limitations

- The evaluation dataset contains only six questions.
- Each relevant test question currently has one expected FAQ.
- More English, Roman Urdu, spelling variation, and ambiguous questions should be tested.
- The current reranker uses lexical overlap rather than a separately trained reranking model.
- Threshold performance should be reevaluated with a larger dataset.

## 9. Conclusion

The advanced retrieval implementation successfully supports semantic, lexical, and hybrid retrieval, query normalization, metadata filtering, reranking, and unrelated-query rejection.

All three methods achieved the same evaluation metrics on the current test dataset. The implementation is ready for further testing with a larger FAQ evaluation dataset.
