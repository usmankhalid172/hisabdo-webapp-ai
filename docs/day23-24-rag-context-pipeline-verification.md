# Day 23-24 — RAG Context Pipeline Setup: Retrieval Context Verification Notes

**Intern:** Muhammad Hamza Nawaz
**Subtask:** Wire up RAG context pipelines and LLM prompt chains; verify that context retrieval
correctly formats system inputs before hitting backend response handlers
**Branch:** `feature/task23-24-llm-rag-hamza`
**Base:** `main` (per Day 23-24 branching rule — a repo-wide reset point, not a continuation of
the Day 15-22 branch chain)

---

## 1. Design Decision (read this first)

As of Day 23-24, **two independent retriever implementations already exist** in this repo with
no team decision on which is canonical:
- Ahmed Ali Ghori's `rag.py` / `retriever.py` / `knowledge_base.py` (flat, in
  `src/financial_assistant/`)
- Faiza Asif's `rag/` package (`rag/retriever.py`, `rag/knowledge_base.py`)

Building a third concrete retriever here would be a fourth independent implementation of the
same responsibility. Instead, this deliverable is the **prompt-chain integration module** the
task literally asks for: a pipeline that accepts retrieved context in a minimal, retriever-agnostic
shape, validates/ranks/formats it, and hands it to the existing (unchanged) LLM request layer.
Whichever retriever the team eventually picks can plug into this pipeline by mapping its output
to a 3-field shape (`text`, `source`, `score`) — no changes to this module required.

## 2. What Was Built

**New module:** `src/financial_assistant/rag_pipeline.py`

- `ContextChunk` — minimal retrieved-context shape (`text`, optional `source`, optional `score`).
  Accepts either this dataclass or a plain dict, so either existing retriever's output maps in
  with a one-line adapter.
- `prepare_context()` — normalizes raw chunks, drops malformed ones without failing the whole
  request, ranks by score (unscored chunks sort last), caps chunk count and total character
  budget.
- `format_context_block()` — formats prepared chunks into a labeled block ("Relevant financial
  data: [1] (source) text ..."). This is the "correctly formats system inputs" requirement.
- `build_grounded_question()` — prepends the context block to the user's question; returns the
  question unchanged when there's no context (ungrounded fallback, not an error state).
- `get_grounded_financial_assistant_response()` — the public entry point. Normalizes context,
  builds the grounded question, and hands off to `llm_service.get_financial_assistant_response`
  **unchanged** for everything downstream (validation, retry, rate-limit handling, inconsistent-
  response detection, fallback — all Day 15-22 work, reused as-is, not duplicated).

**Small supporting refactor in `llm_service.py`:** extracted the message-sending call into
`_call_llm_api_with_messages()` so custom message lists can reuse the same tested error-handling
path. Not currently used by `rag_pipeline.py` (which took the simpler route of concatenating
context into the single user message, matching `llm_service.py`'s existing single-user-message
design) — kept as available infrastructure for a future prompt-chain design that needs distinct
message roles (e.g. a separate "context" role) without another refactor.

## 3. Retrieval Context Verification (evidence)

Verified end-to-end with a mocked LLM client (see `tests/test_rag_pipeline.py`,
`test_grounded_response_reaches_llm_with_formatted_context`): captured the actual message list
sent to `client.chat.completions.create` and confirmed the user message contains the formatted
context block, the source label, and the original question — i.e., retrieved context reaches the
backend response handler correctly formatted, exactly as this task requires.

| Check | Result |
|---|---|
| Dataclass chunk accepted | Pass |
| Plain dict chunk accepted (either retriever's likely output shape) | Pass |
| Malformed chunk (missing/empty text, wrong type) dropped, not fatal | Pass |
| All-malformed input degrades to empty context, not an error | Pass |
| Chunks ranked by score, descending; unscored sort last | Pass |
| Chunk count capped at config limit | Pass |
| Chunks below `min_chunk_score` filtered out | Pass |
| Oversized context truncated to character budget | Pass |
| Empty context formats to empty string (no context block, no crash) | Pass |
| Context block includes numbered labels and source names | Pass |
| Multiple chunks numbered in order | Pass |
| No-context question passes through unchanged | Pass |
| Context block prepended before the question, correctly delimited | Pass |
| Grounded question reaches the LLM API call with context formatted correctly | Pass |
| Ungrounded call behaves identically to the pre-existing Day 15-22 flow | Pass |
| Grounded call still falls back gracefully on API failure | Pass |

## 4. Test Results

- `tests/test_rag_pipeline.py`: **17 passed** (new, this cycle)
- Full repo suite: **46 passed, 4 skipped-with-reason, 0 failed** (confirms zero regression
  across Days 15-22)

## 5. Known Limitations

- No real retriever wired in — verified against hand-built sample context chunks, since no
  canonical retriever has been chosen (see Section 1). Once one is selected, the only work
  needed is a small adapter mapping its output to `ContextChunk`.
- Single-user-message design (context concatenated into the question) rather than a distinct
  message role — matches `llm_service.py`'s existing design; would need a small extension if the
  team wants context in its own message role instead.
- No live LLM API key — all evidence is mocked, consistent with every prior day.
- Character budget (3000 chars default) and chunk cap (5 default) are reasonable defaults, not
  tuned against real retrieval volume or cost data — worth revisiting once a real retriever and
  usage pattern exist.

## 6. What Is NOT Ready for SQA Yet

Per the Day 21-22 operating plan's AI/ML → SQA handoff format:
- **Not ready:** end-to-end grounded chatbot behavior (depends on a canonical retriever being
  selected and wired in — this pipeline is the connective layer, not the retriever itself).
- **Ready for isolated testing:** `rag_pipeline.py`'s own contract — chunk normalization,
  ranking, capping, and formatting can be tested independently of any retriever, using the same
  hand-built chunk fixtures this module's own tests use.

## 7. Evidence

- Branch: `feature/task23-24-llm-rag-hamza`
- New: `src/financial_assistant/rag_pipeline.py`, `tests/test_rag_pipeline.py` (17 passed)
- Modified: `src/financial_assistant/llm_service.py` (internal refactor only, no behavior change
  — confirmed by full existing suite still passing unchanged)
- This document