# Department 3 Chunking and Embedding Configuration Decisions

## 1. Content-specific chunking

The following are **initial, token-count-based staging defaults**, not empirically proven optima. The supplied HisabDo FAQ dataset is short-form and does not contain a representative approved corpus of accounting tables, workflows, and long manuals. Tune these values only after labeled retrieval evaluation.

| Content type | Chunk target | Overlap | Boundary strategy |
|---|---:|---:|---|
| Structured FAQs | 250 tokens | 30 tokens | Keep question/title with answer; normally one chunk per FAQ |
| Accounting feature tables | 350 tokens | 40 tokens | Preserve header + complete row groups; do not split a row |
| Workflow guidelines | 450 tokens | 60 tokens | Split at numbered step/heading boundaries; retain prerequisites and warnings |
| Long-form user documentation | 600 tokens | 80 tokens | Split by section/paragraph; carry section heading into each chunk |

The script uses whitespace-delimited token counting as a deterministic proxy for initial chunk sizing. It is not a model tokenizer. Before production, replace/validate the proxy against the exact embedding tokenizer and add table-aware row packing if real table sources are introduced.

## 2. Embedding model and vector parameters

| Parameter | Decision / current evidence |
|---|---|
| Model repository ID | `sentence-transformers/all-MiniLM-L6-v2` |
| Output dimension | 384 |
| Runtime wrapper in live retriever | `langchain_huggingface.HuggingFaceEmbeddings` |
| Device | CPU (`model_kwargs={"device": "cpu"}`) |
| Normalization | L2 (`encode_kwargs={"normalize_embeddings": true}`) |
| Similarity | Cosine similarity |
| Staging vector dtype | float32 |
| Staging index | Exact flat matrix; no ANN graph/tree parameters |
| Live vector store | LangChain `InMemoryVectorStore`; in-memory, non-persistent |
| Live retrieval defaults | relevance threshold 0.40; `retrieve(..., top_k=3)` |
| Model revision | **Not pinned in the supplied repository snapshot** |
| Package versions | Current environment snapshot: `requirements-lock-current.txt`; key versions: sentence-transformers 5.7.0, transformers 5.19.0, torch 2.14.1, huggingface-hub 1.33.0, langchain-huggingface 1.2.3, langchain-core 1.6.10, numpy 1.26.4, scikit-learn 1.5.2 |

The model ID and dimension are visible in `src/financial_assistant/faq_rag.py`; CPU and normalization are configured in the same file. `requirements-lock-current.txt` records the installed environment using `pip freeze`; `python -m pip check` reported `No broken requirements found`. This is an environment snapshot, not yet a verified project-only or cross-platform lockfile. The Hugging Face model commit SHA remains unpinned, and no real embedding build has been completed. Therefore exact model-revision and end-to-end reproducibility are still pending.

The staging script refuses an embedding build unless `--model-revision` is supplied as a commit SHA. Example after the team has approved a real SHA:

```powershell
python scripts\department3_ingestion.py --build-embeddings --model-revision <APPROVED_HUGGING_FACE_COMMIT_SHA>
```

Do not substitute a guessed SHA. Commit a lockfile generated from the approved build environment before declaring cross-environment reproducibility.

## 3. Why no vector DB tuning is claimed

The live HisabDo FAQ retriever uses LangChain `InMemoryVectorStore`, not FAISS, Chroma, Pinecone, or pgvector. It has no configured ANN `nlist`, `nprobe`, `M`, `efConstruction`, or `efSearch` parameters. The new staging output stores a flat exact vector matrix; approximate-index tuning is not applicable at this stage.

## 4. Retrieval configuration decision

Keep the live verified-only filter. Retain the existing 0.40 threshold and top_k=3 as current code defaults onlyâ€”not as proven optimal values. Existing comparison documentation describes a separate TF-IDF experiment with a 0.12 baseline and seven diagnostic queries; it explicitly does not establish a globally optimal threshold. Do not mix that experimental TF-IDF configuration with the live sentence-transformer retriever.

## 5. Required next measurements

Build a representative, approved evaluation set with relevance labels for each content type. Compare candidate chunk sizes/overlaps using recall@k, precision@k, MRR, irrelevant-context rate, chunk count, embedding latency, and index build time. Select settings based on those results rather than intuition alone.

## Final validation update — 2026-11-11

### Actual staged data
- Source records: 20
- Approved staged documents: 12
- Excluded unverified/unapproved records: 8
- Current staged content types: FAQ only (12 chunks)
- FAQ chunk text length: 97–450 characters
- Configured FAQ chunk size/overlap: 250 / 30
- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Model revision: 1110a243fdf4706b3f48f1d95db1a4f5529b4d41
- Vector matrix: 12 x 384, float32
- Normalization: L2; all vectors finite, non-zero and normalized
- Similarity: cosine
- Staging index: flat exact matrix
- Embedding build: successful

### Chunking optimization limitation
The current approved source set contains FAQs only. Accounting feature tables, workflow guidelines and long-form user documentation were not represented in the approved staged sample. Their proposed chunk sizes and overlaps remain provisional and must not be described as empirically optimized. A representative approved sample and labeled retrieval evaluation are required before finalizing those content-type settings.

### Fresh staged retrieval evaluation
- Dataset: 60 questions from docs/evaluation/retrieval_results_v1.0.csv
- MATCH: 28
- MISS: 13
- REVIEW: 8
- SAFE_ABSTENTION: 11
- In-scope expected-source match rate: 68.29% (28/41)
- Detailed results: docs/evaluation/department3_staged_retrieval_results_v1.0.csv
- Evaluation report: docs/evaluation/department3_staged_retrieval_report_v1.0.md

This is a separate staged-vector benchmark. It is not directly comparable to the historical live FaqRetriever result of 73.17%, and it does not measure chatbot answer accuracy.

### Remaining approval and validation
- Obtain representative approved accounting-table, workflow and long-document samples.
- Tune and compare chunk size/overlap using those samples and labeled retrieval cases.
- Complete independent source-owner approval before promoting staged content to the live knowledge base.

## Corpus-based chunk validation — 2026-11-11

- Current approved staged corpus: 12 documents, all classified as FAQ.
- Configured FAQ chunk parameters: 250 tokens with 30-token overlap.
- Observed chunk text lengths: 97–450 characters.
- All 12 staged chunks currently use the FAQ configuration.
- No approved accounting feature tables, workflow guidelines or long-form documentation were available for empirical testing.
- The 350/40, 450/60 and 600/80 settings remain proposed initial configurations for their respective content types, not empirically validated optimal values.
- Chunk optimization across all four content types remains pending representative approved samples and retrieval evaluation.
- The token-count implementation uses a whitespace-based proxy; it should not be described as exact model-token counting.
