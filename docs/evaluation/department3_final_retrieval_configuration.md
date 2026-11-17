# Department 3 Final Retrieval Configuration

## Candidate configuration evaluated

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- Vector metric: cosine similarity
- Embedding vectors: existing normalized 384-dimensional vectors
- Lexical retrieval: BM25 (k1=1.5, b=0.75)
- Hybrid fusion: Reciprocal Rank Fusion (RRF, k=60)
- Query normalization: lowercase, punctuation/token normalization, typo map, Roman Urdu phrase aliases
- Metadata eligibility: verified-only, intent-specific, fail-closed candidate filtering.
- Reranking: deterministic lexical overlap bonuses; optional experiment, not enabled in the recommended default pipeline.
- Tested top-k values: 1, 3, 5
- Provisional dense baseline threshold: cosine >= 0.40; not calibrated or deployment-approved.

## Safety and metadata rules

- Only verified/approved source records count as positive evidence.
- Unverified expense-categorization draft `faq-002` must not be promoted to approved evidence.
- `faq-005` confirms PDF reports for supported records; it does not confirm CSV export or exact screen-by-screen steps.
- Do not use expected source IDs to filter retrieval candidates; they are evaluation labels only.
- If no verified passage supports the requested feature or workflow, abstain rather than invent instructions.
- Expense-categorization intent includes English, Roman Urdu, category-list and common misspelling variants.
- Current approved candidate set for expense categorization is empty; faq-002 remains unverified and excluded.
- Expense-reporting intent is restricted to verified faq-005; PDF support does not establish CSV export or exact UI steps.

## Calibration status

No calibrated universal relevance threshold has been established. The 0.40 dense threshold is provisional only. Validate score distributions against false positives, verified relevance and safe abstention before deployment.
