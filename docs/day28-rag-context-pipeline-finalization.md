# Day 28 — RAG Context Pipeline: Finalization & Context Assembly Test Notes

**Intern:** Muhammad Hamza Nawaz
**Task:** Complete the RAG context formatting pipeline. Ensure retrieved document context
chunks are efficiently structured and bounded within prompt length limits prior to final
deployment integration.
**Branch:** `feature/task28-llm-rag-hamza`
**Base:** `feature/task27-llm-rag-hamza` (PR #70)

---

## 1. Status Coming Into Day 28

Bounding context within prompt length limits was already substantially addressed one cycle
early — QA's Day 27 review of PR #70 (Syeda Isma Nazir) found a real bug where a well-populated,
entirely normal grounded question could exceed `llm_service`'s input-length limit and be
rejected. That was fixed and verified before Day 28 started (see PR #70). Day 28's remaining
gap, once that fix was in place, was **efficiency of structuring**, not boundedness — specifically,
duplicate content wasting prompt budget.

## 2. What Was Completed This Cycle

### Chunk deduplication (`prepare_context`, `rag_pipeline.py`)
A retriever can legitimately return the same underlying content more than once — matched by
multiple query terms, indexed twice, etc. Previously, duplicate chunks were not detected, so
identical text could consume prompt budget twice for no added information. Now, exact-duplicate
chunk text is deduplicated before ranking/capping, keeping the highest-scored occurrence.
Near-duplicate but genuinely distinct content (e.g. two different transactions at the same
merchant on different dates) is explicitly **not** collapsed — dedup is exact-text-match only, to
avoid silently dropping real information.

### `.env.example` (repo-wide, root)
Per the Day 28 deployment-configuration requirement (any team member modifying model connectors
must document required runtime keys): added `FINANCIAL_ASSISTANT_LLM_API_KEY`, the specific
environment variable `llm_service.py` reads, which was missing from the existing root
`.env.example` (that file only documented `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`, used by a
different module). Documented as optional/blank-safe, since every test in this module's suite
runs against a mocked client and does not require a real key.

## 3. Context Assembly Test Notes (evidence)

| Check | Result |
|---|---|
| Chunks ranked by score, descending; unscored sort last | Pass (Day 23-24) |
| Chunk count capped at configured limit | Pass (Day 23-24) |
| Chunks below minimum score filtered out | Pass (Day 23-24) |
| Oversized total context truncated to character budget | Pass (Day 23-24) |
| **Exact-duplicate chunk text deduplicated, higher score kept** | **Pass (Day 28, new)** |
| **Near-duplicate but distinct chunks both retained (dedup guardrail)** | **Pass (Day 28, new)** |
| Grounded question with realistic near-budget context is not rejected by input-length validation | Pass (fixed Day 27, re-verified Day 28) |
| A caller-supplied larger input limit is never shrunk by the grounded path | Pass (Day 27) |
| Adversarial/malformed chunk content (injection-style text, control characters, oversized single chunks) does not break formatting or budget enforcement | Pass (Day 27) |

## 4. Test Results

- `tests/test_rag_pipeline.py`: 21 passed (19 from Day 23-27 + 2 new dedup tests)
- Full module suite (`test_llm_service.py`, `test_day21_22_error_handling.py`,
  `test_vector_store_day25.py`, `test_vector_store_day26.py`, `test_day27_adversarial_inputs.py`,
  `test_use_cases_day17.py`, `test_rag_pipeline.py`): **72 passed, 4 skipped-with-reason, 0 failed**

## 5. What "Efficiently Structured and Bounded" Means at This Point

- **Bounded:** context is capped by chunk count, per-chunk score, and total character budget —
  and the downstream input-length check that consumes the assembled context can no longer
  silently reject a well-formed grounded question (Day 27 fix).
- **Efficiently structured:** duplicate content no longer consumes budget redundantly (Day 28);
  chunks are consistently labeled, numbered, and source-attributed (Day 23-24); truncation
  happens at the chunk level with a legibility floor (won't keep a truncated fragment under 50
  characters — Day 23-24).
- **Not addressed, and out of this module's scope:** semantic-level redundancy (two chunks that
  say the same thing in different words) — only exact text matches are deduplicated. Catching
  near-semantic duplicates would require actual embeddings, which this environment doesn't have
  access to (see Day 25 known limitations).

## 6. Blockers / Unchanged From Prior Days

- No canonical retriever decision from the team — still unresolved since Day 17.
- No live LLM API key at any point across this project.
- The live deployment (`hisabdo-webapp-ai.onrender.com`) currently routes its chatbot endpoint
  through Ahmed Ali Ghori's `service.py`/`llm_providers.py`/`rag/` implementation, not this
  module — this module's pipeline is validated and ready, but not yet the one actually serving
  requests. Worth a team decision now that there's a live, visible deployment where this choice
  has a real user-facing effect, not just a branch-level one.

## 7. Evidence

- Branch: `feature/task28-llm-rag-hamza`
- Modified: `src/financial_assistant/rag_pipeline.py` (dedup), root `.env.example`
  (documentation)
- Updated: `tests/test_rag_pipeline.py` (21 passed, 2 new)
- This document