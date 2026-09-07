# Day 25 — RAG Context Pipeline Setup: Vector Database Retrieval Verification Notes

**Intern:** Muhammad Hamza Nawaz
**Task:** Wire up vector database retrieval with LLM prompt templates. Verify that context
retrieval correctly formats transaction histories or system inputs before feeding them into
backend response handlers.
**Branch:** `feature/task15-25-llm-rag-hamza`
**Base:** `feature/task23-24-llm-rag-hamza`

---

## 1. Relationship to Day 23-24

This task is the same "RAG Context Pipeline Setup" responsibility as Day 23-24, with one added
requirement: actual vector-database-style retrieval, over transaction data specifically. Day
23-24 deliberately built the pipeline (`rag_pipeline.py`) against a retriever-agnostic contract
without implementing a concrete retriever, since two independent ones (Ahmed's, Faiza's) already
existed with no team decision on which is canonical. That decision still hasn't been made as of
Day 25. This task is answered by implementing a **working reference retriever** that plugs into
the existing contract — not a claim that it should be *the* canonical one, and not a rebuild of
the pipeline itself.

## 2. What Was Built

**New module:** `src/financial_assistant/vector_store.py`

- `Transaction` — a transaction record (id, date, amount, category, merchant, note) with
  `to_retrievable_text()` (what gets indexed/matched against) and `to_display_text()` (the
  consistently formatted line that ends up in a retrieved context chunk).
- `TransactionVectorStore` — an in-memory store using bag-of-words term-frequency cosine
  similarity as a dependency-free stand-in for real vector embeddings (no external vector DB or
  embeddings API is available in this environment). `.add()` / `.query()` mirror the shape a real
  vector DB client call would have, so swapping in a real one later means replacing this class's
  internals only.
- `build_sample_transaction_store()` — a small synthetic dataset (10 sample transactions) used to
  verify the pipeline end-to-end. Clearly demo data, not a real data source.
- `.query()` returns results already shaped as `rag_pipeline.ContextChunk` — zero changes needed
  to Day 23-24's pipeline to consume them.

## 3. Retrieval Context Verification (evidence)

Confirmed end-to-end (`tests/test_vector_store_day25.py`,
`test_vector_retrieval_reaches_llm_correctly_formatted`): queried the store, ran the results
through `rag_pipeline`'s formatting, and inspected the actual message sent to the (mocked) LLM
API — confirmed it contains the formatted context block, transaction details, and the source
label, exactly as this task requires.

| Check | Result |
|---|---|
| Empty store returns no results (not an error) | Pass |
| More relevant transactions rank higher than less relevant ones | Pass |
| Results carry source label and similarity score | Pass |
| `top_k` correctly limits result count | Pass |
| Irrelevant query returns no results (no false positives) | Pass |
| Transaction formats to a consistent, readable line | Pass |
| Retrieved context reaches the LLM call correctly formatted | Pass |
| No matching transactions falls through to ungrounded (not an error) | Pass |

## 4. Test Results

- `tests/test_vector_store_day25.py`: **8 passed**
- Full repo suite: **54 passed, 4 skipped-with-reason, 0 failed**

## 5. Known Limitations

- Bag-of-words cosine similarity, not real embeddings — adequate to verify the pipeline
  mechanics, but weaker at genuine semantic matching (e.g. won't match "food shopping" to
  "groceries" without a shared word) than a real embedding model would.
- Sample data only, 10 synthetic transactions — no real transaction data source is wired in.
- In-memory, non-persistent — rebuilt fresh each process start.
- Retriever-canonicalization question (this vs. Ahmed's vs. Faiza's) still unresolved.

## 6. Evidence

- Branch: `feature/task15-25-llm-rag-hamza`
- New: `src/financial_assistant/vector_store.py`, `tests/test_vector_store_day25.py` (8 passed)
- Reused unchanged: `src/financial_assistant/rag_pipeline.py`, `src/financial_assistant/llm_service.py`
- This document