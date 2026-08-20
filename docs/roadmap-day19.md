# Day 19 — Chatbot / RAG Technical Status & Roadmap to Day 30

**Status date:** 2026-08-21
**Branch:** `feature/ahmedali-ghori-ai-chatbot` /
`feature/ahmedali-ghori-chatbot-days17-20-completion`
**Base branch:** `main` (Team Lead review required for merge)

---

## 1. What is completed (working code, verified)

| Area | Evidence (not estimates) |
|---|---|
| Chatbot pipeline (intent → facts → retrieval → response → validation) | `src/financial_assistant/` (engine, intents, processor, transactions, responders, response_validator) |
| RAG baseline (chunking + metadata + keyword/tag retrieval) | `knowledge_base.py`, `retriever.py`, `rag.py`, `research/rag-approach.md` |
| Optional LLM polish with offline fallback | `llm.py`, `.env.example` (fake key only) |
| FastAPI service + Pydantic schemas | `src/integration/app.py`, `src/integration/schemas.py` |
| CLI demo | `src/financial_assistant/cli.py` |
| Tests | **63/63 pass** (`python -m unittest discover -s tests -t . -v`) |
| Lint | **clean** (pyflakes on `src tests scripts`) |
| Sample queries + API evidence | `docs/evidence/terminal-and-api-output.txt`, `scripts/run_verification.py` |
| Day 15 architecture/RAG notes | `docs/chatbot-implementation.md`, `research/rag-approach.md` |
| Day 17 use-case verification | `docs/day17-use-case-verification.md` |
| Day 18 integration flow | `docs/integration-service-flow.md` |

## 2. What is in progress

- Repository push/PR creation — blocked on GitHub 403 (see section 4).
- Team alignment with Rameesha (prompts/test cases), Farheen (RAG research),
  Niha (AI service boundaries) — documents align; live merge pending review.

## 3. What is pending (not started)

| Item | Notes |
|---|---|
| Budgets & remaining-budget queries | Needs budget dataset + computation |
| Transaction-history listing / month & category comparisons | New intents + aggregation logic |
| Multi-turn conversation memory | Requires session state store |
| Vector/embedding retrieval + hybrid rerank | Planned experiment; needs dependency + eval set |
| Production data integration | Real transaction schema pending approval |

## 4. Known blockers / dependencies

| # | Blocker | Status / action |
|---|---|---|
| 1 | **GitHub push 403** (re-checked 2026-08-21, still denied for `AHMEDALIGHORI`) | Report to Team Leads; account must be added as collaborator on `usmankhalid172/hisabdo-webapp-ai` |
| 2 | No OpenAI API key in dev env | Not blocking — deterministic pipeline is primary, fully tested |
| 3 | Port 8000 conflict locally | Workaround: `--port 8010` |
| 4 | Keyword+tag retrieval is the baseline | Embedding path scaffolded in `rag.py`; Day-30 experiment |
| 5 | Budgets dataset missing | Blocks budget use cases only |

Full details: `docs/blockers-and-dependencies.md`.

## 5. Unresolved technical issues

1. LLM-polish path never exercised live (no key) — will validate once a key is
   provided or via a mocked provider test.
2. Retrieval quality for paraphrases/typos — keyword overlap only; embeddings
   planned to fix.
3. Stateless engine — follow-up questions ("and last month?") are not
   resolved; needs memory design (in-memory session → DB-backed).
4. Shared-state safety already handled (per-request instance for
   `reference_date`), but a session-id-based design is still required for
   multi-turn.

## 6. Roadmap toward Day 30

1. **Get push access unblocked** (Team Leads) → push branches, open PRs
   (`feature/ahmedali-ghori-ai-chatbot`,
   `feature/ahmedali-ghori-chatbot-days17-20-completion`).
2. Implement budgets + remaining-budget answering (new dataset + intent +
   responders + tests).
3. Add history-listing and month/category comparison intents.
4. Embedding retrieval (cosine) + hybrid rerank, with a labelled evaluation
   set to measure before/after.
5. Multi-turn memory (session store) with session-id in `ChatRequest`.
6. Integrate real HisabDo backend data flow once schema approved.
7. Final Day-30 evidence pack: tests, API traces, screenshots, blocker log.

## 7. Related GitHub branches / commits

- `feature/ahmedali-ghori-ai-chatbot` (local) — chatbot implementation:
  `c07217a` (implementation), `7dc9f75` (docs + use-case matrix),
  `ff26c3a` (403 blocker record), `1fba2b2` (Day 16 features + validation).
- `main` (local) additionally contains `5812d64` (lint fixes).
- `feature/ahmedali-ghori-chatbot-days17-20-completion` (this branch) —
  Day 17-20 completion docs + status.
- Remote status: **nothing pushed yet** — 403 blocker prevents it (see
  `docs/blockers-and-dependencies.md` section 3).