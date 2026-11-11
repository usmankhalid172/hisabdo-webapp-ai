# Department 3 Chunking and Embedding Configuration

## 1. Current implementation

The current Department 3 FAQ retrieval implementation uses scikit learn TF IDF vectorization and cosine similarity.

| Setting | Current value |
|---|---|
| Library | scikit learn |
| Library version | 1.5.2 |
| Vectorizer | sklearn.feature_extraction.text.TfidfVectorizer |
| stop_words | english |
| Similarity | cosine similarity |
| FAQ relevance threshold | 0.30 |
| FAQ retrieval corpus | title and text |
| FAQ corpus refresh | Rebuilds vectorizer and document matrix |
| Neural embedding model | Not configured |
| Embedding model version | Not applicable |
| Embedding dimensions | Not applicable |
| External vector database | Not configured |
| Persistent vector index | Not configured |

The transaction vector store is a separate dependency free in memory implementation using token frequency counters and cosine similarity. It is not a neural embedding index.

## 2. Proposed content specific chunking

The following are proposed character based targets for future long form source ingestion. They are not claims about the current TF IDF retrieval implementation.

| Content type | Proposed strategy | Target size | Overlap |
|---|---|---:|---:|
| Structured FAQs | One complete record | No split | 0 |
| Financial concepts | Question, answer and keywords together | No split | 0 |
| Accounting feature tables | Header and related rows together | 1000 | 0 |
| Workflow guidelines | Paragraph boundary splitting | 1000 | 120 |
| Long user documentation | Heading and paragraph boundary splitting | 1500 | 180 |

Short FAQ records currently range from 74 to 298 characters. Splitting them would separate context unnecessarily.

Financial concept records must retain the question, answer and keywords in one chunk. The ingestion script applies this structure.

## 3. Source and index reproducibility

The ingestion script records:
- Source file paths.
- SHA 256 hashes of source records.
- Chunk IDs and document IDs.
- Source metadata.
- Chunking configuration.
- scikit learn version declared by the execution configuration.

The current manifest is data/department3_ingestion_manifest.json.

The generated chunks are data/structured_knowledge_chunks.json.

## 4. Important distinction

No neural embedding package or model is configured in the inspected project files. No vector dimensions, ANN index type, distance metric for a persistent index, or index construction parameters can honestly be documented as implemented.

The current FAQ system uses TF IDF and cosine similarity. Its feature space is fitted from the current FAQ corpus. The transaction vector store uses term frequency counters and cosine similarity.

A future neural embedding deployment must record the exact model identifier, immutable model revision, tokenizer revision, vector dimensions, normalization setting, embedding batch size, and inference library version.

A future persistent vector index must record the database and version, collection name, distance metric, index type, construction parameters, search parameters, metadata schema, and persistence settings.

These future values must be measured and approved before they are added as production configuration.

## 5. Validation evidence

Current source counts:
- FAQ records: 12.
- Financial knowledge records: 6.
- Generated chunks: 18.
- Unique chunk IDs: 18.

Financial chunk content was checked to confirm that question, answer and keywords are preserved.

Full test suite:
- 325 passed.
- 4 skipped.
- 1 warning.
- 0 failed.

## 6. Limitations

The current ingestion script processes local JSON source files. It does not fetch remote pages, ingest standalone long form documentation, or build neural embeddings or an external vector index.

The long form chunk sizes above are proposed settings. They require implementation and validation against approved workflow and documentation sources before being treated as active settings.
