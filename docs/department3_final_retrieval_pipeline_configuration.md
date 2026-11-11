# Department 3 Final Retrieval Pipeline Configuration

## Status
Recommended experimental configuration. This is not production clearance.

## Pipeline

1. Receive the user query after authentication and safety checks.
2. Normalize case, whitespace, punctuation and common English word forms.
3. Preserve the original query. Apply only documented vocabulary rewrites that do not change the user's intent.
4. Retrieve candidates using BM25 and TF IDF.
5. Combine scores using the tested hybrid formula.
6. Rank candidates by the combined score.
7. Apply the calibrated experimental threshold.
8. Return at most three evidence passages, provided each passage passes the threshold and source approval checks.
9. If evidence is insufficient, ask a clarification question or abstain.
10. Never use retrieved FAQ text to supply personal account balances, expenses or other live financial values. Those must come from the authenticated backend.

## Tested scoring formula

Base hybrid score:

`base_hybrid_score = 0.5 * (bm25_score / (bm25_score + 5.0)) + 0.5 * tfidf_cosine_score`

Experimental feature intent score:

`final_score = base_hybrid_score + 0.20`

The 0.20 bonus applies only when the query and candidate document match the tested export or categorization intent terms.

TF IDF uses scikit learn `TfidfVectorizer`, English stop words and unigram plus bigram features. BM25 is a local implementation with k1 = 1.5 and b = 0.75. The corpus contains 12 records.

## Recommended experimental settings

| Setting | Value |
|---|---|
| Candidate retrieval | BM25 plus TF IDF |
| BM25 weight | 0.50 |
| TF IDF weight | 0.50 |
| BM25 fixed score transform | score / (score + 5.0) |
| Context top k | 3 maximum, each passage independently checked |
| Experimental minimum top 1 score | 0.45, feature intent 0.20 scoring |
| Metadata filtering | Disabled as a global hard filter |
| Query normalization | Conservative normalization only |
| Query expansion | Disabled by default; synonym expansion benchmarked separately |
| Reranking | Experimental feature intent boost 0.20; lexical overlap reranker disabled |
| No evidence behavior | Clarify or abstain |
| Personal financial values | Authenticated backend only |

## Evidence and safety rules

A score threshold alone cannot prove that a passage contains the exact rule or feature specification. Before generation, verify that the passage belongs to an approved source and supports the requested feature. Use expected source records only for offline evaluation, never as runtime routing instructions.

Do not answer unsupported Khata, Udhar, payables, phone number, official URL or privacy ownership questions from unrelated passages. Do not infer missing product behavior.

For expense export questions, preserve the caveat that the current FAQ describes CSV and PDF export through Reports, but live application behavior remains unverified.

## Limitations

The available environment did not contain sentence transformers, transformers or a dense embedding model. Dense semantic retrieval was therefore not benchmarked. The tested hybrid is BM25 plus TF IDF, not BM25 plus dense vectors.

The threshold was calibrated on 71 evaluation cases and a 12 record corpus. It must be rechecked against a larger, independently reviewed set before production use.
