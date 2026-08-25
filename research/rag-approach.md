# RAG Approach — AI Financial Assistant

**Branch:** `feature/ahmedali-ghori-ai-chatbot`
**Aligned with:** `feature/farheen-fatima-rag-ml-research-day15` (team RAG research).

---

## 1. Design decision

We implemented the **simple baseline recommended by the team research**:

1. **Document chunking with metadata** — `data/saving_tips.md` is split on
   `## ` headings into chunks; each chunk carries `tags` metadata
   (`knowledge_base.py`).
2. **Hybrid retrieval (keyword overlap + tag/metadata score)** —
   `retriever.py` scores every chunk with:
   - text-overlap score: `2 * |query ∩ chunk_tokens| / (|query| + |chunk|)`
   - tag score: overlap between query tokens and the chunk's tag tokens
   - final = text + tag; top-K (default 3) with a `min_score` floor.
3. **Backend calculations** — monetary answers never come from the LLM; they
   are computed deterministically (`transactions.py`) and injected as
   grounding facts. This directly implements the research note:
   *"Perform financial calculations through the backend instead of the LLM."*
4. **Grounded prompts** — the optional LLM turn receives only computed facts +
   retrieved context (`prompts.py`); the system prompt forbids invented figures.
5. **Fallback responses** — no context above threshold → friendly "I could not
   find …" instead of hallucination.

---

## 2. Sample retrieval results (evidence)

| Query | Retrieved (top-2, scores) |
|-------|---------------------------|
| "How can I save money?" | Reduce dining-out costs to save, Cut grocery spending to save |
| "Give me saving tips" | Budgeting to save money |

An unrelated query ("which movie won the oscar") returns **≤ 1 chunk** because
of the `min_score` threshold → assistant falls back safely.

---

## 3. Known limits / next experiments

| Experiment | Why | Status |
|-----------|-----|--------|
| Embeddings + vector store (cosine) | Robust to paraphrase/wording | Planned — needs dependency + eval set |
| Hybrid vector + keyword rerank | Correct mixed-query results | Planned after baseline eval |
| Metadata filtering on period/category | E.g., "saving tips for groceries" | Partial (tags exist; not yet period-aware) |
| Retrieval eval set (relevance labels) | Measure before/after | Planned |

---

## 4. Cost / latency notes (recorded)

- Current pipeline is **offline** → ~0 latency, 0 API cost.
- Optional LLM pass: 1 small `gpt-4o-mini` call per turn alone if enabled;
  30 s timeout; any failure falls back to the deterministic answer.