# Department 3 Automated Ingestion Execution Report

Execution time: 2026-11-11T01:35:02.675221+00:00
Status: PASS

## Source results

| Source | Records read |
|---|---:|
| data/faq_docs.json | 12 |
| data/sample_financial_knowledge.json | 6 |

## Change detection

New records: 1
Modified records: 0
Deleted records: 0
Unchanged records: 17
Generated chunks: 18
Duplicate IDs: 0
Duplicate content within source: 0
Failed source files: 0
Parsing and record errors: 0

## Errors and duplicates

No errors or duplicates detected.

## Reproducibility configuration

```json
{
  "chunking_unit": "characters",
  "faq": {
    "strategy": "one_complete_record",
    "max_size": 0,
    "overlap": 0
  },
  "financial_concept": {
    "strategy": "question_answer_keywords_together",
    "max_size": 0,
    "overlap": 0
  },
  "feature_table": {
    "strategy": "header_and_related_rows",
    "max_size": 1000,
    "overlap": 0
  },
  "workflow_guidelines": {
    "strategy": "paragraph_boundary",
    "max_size": 1000,
    "overlap": 120
  },
  "long_documentation": {
    "strategy": "heading_and_paragraph_boundary",
    "max_size": 1500,
    "overlap": 180
  },
  "current_retrieval": {
    "vectorizer": "sklearn.feature_extraction.text.TfidfVectorizer",
    "scikit_learn_version": "1.5.2",
    "stop_words": "english",
    "similarity": "cosine",
    "relevance_threshold": 0.3,
    "neural_embedding_model": null,
    "external_vector_index": null
  }
}
```

## Scope and limitations

Sources currently include local JSON files only. Remote web pages are not fetched.
The current retrieval implementation uses TF IDF, not a neural embedding model.
No external vector database or persistent vector index is configured.
The manifest records content hashes for repeatable change detection.
A deleted source file is reported as a failed source, not treated as an empty source.
Chunk output is regenerated from successfully parsed records. Review errors before publishing.
