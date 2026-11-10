# Department 3 Chunking and Embedding Configuration

## Scope
This configuration is for HisabDo Department 3 knowledge ingestion.
The active data/faq_docs.json is not modified. Staging data is the input.

## Content-specific chunking decisions

| Content type | Strategy | Overlap |
|---|---|---|
| Structured FAQ | One question and answer per chunk | 0 |
| Accounting feature table | Preserve table headers with related rows | 0 |
| Workflow guidelines | Keep related ordered steps together | 0 |
| Long-form documentation | 450-word target | 75 words |

The current staging set contains 6 FAQ records and 10 financial
knowledge records. It does not contain representative accounting
tables, workflow documents, or long-form documents. Those strategies
are design defaults and have not been empirically benchmarked.

## Embedding and retrieval evidence

HisabDo faq_rag.py currently declares text-embedding-3-small.
This is a provider model alias, not an immutable model revision.
The code does not pin a provider revision or explicitly record the
returned model name and vector dimension.

The FAQ retriever normalizes vectors as float32 and uses dot product.
For normalized vectors, dot product is equivalent to cosine similarity.

The retriever also has a TF-IDF fallback. This is a different vector
space and must not be mixed with OpenAI embedding vectors.

The separate XICTEK website assistant currently uses
scikit-learn TfidfVectorizer, despite its configuration metadata
naming a Sentence Transformers model. That metadata does not prove
that Sentence Transformers generated the vectors.

## Reproducibility record

- Python used during inspection: 3.13.9
- Declared scikit-learn: 1.5.2
- Observed scikit-learn: 1.7.2
- Declared NumPy: 1.26.4
- Observed NumPy: 2.3.5
- Declared OpenAI SDK: openai>=1.0.0
- Observed OpenAI SDK: 3.29.0
- Declared pytest: 8.3.3
- Observed pytest: 8.3.3

The installed environment differs from declared dependency versions.
Exact environment reproducibility is therefore not yet established.

## Index parameters and limitations

The current FAQ retriever computes embeddings in memory at startup.
No persistent FAQ vector index parameters or immutable embedding
revision are established by the inspected implementation.
The Department 3 staging ingestion script does not generate vectors.
It records deterministic content hashes and produces chunks and reports.
