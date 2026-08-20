# Day 20 — Finalized Chatbot / RAG POC & Remaining Technical Blockers

**Status date:** 2026-08-21
**Branch:** `feature/ahmedali-ghori-chatbot-days17-20-completion`
**Workstream:** AI Financial Assistant / Chatbot (RAG / NLP) — Days 15-20

---

## 1. Finalized state of the POC

The AI Financial Assistant / Chatbot RAG POC is **complete and working
offline-first** (no API key required). Verified on 2026-08-21:

- **63/63 tests pass** (`python -m unittest discover -s tests -t . -v`)
- **Lint clean** (`pyflakes` over `src`, `tests`, `scripts`)
- **Verification script runs** (`python scripts/run_verification.py`) with the
  full use-case battery, including live API responses via FastAPI TestClient
- **Supported use cases work**: monthly expense (this/last month), highest
  spending category, spending summary, saving-tip requests (RAG retrieval),
  out-of-scope safe fallback, ambiguous-question clarification

Evidence files:
- `docs/evidence/terminal-and-api-output.txt`
- `docs/day17-use-case-verification.md`
- `docs/chatbot-implementation.md`
- `docs/integration-service-flow.md`
- `docs/roadmap-day19.md`

## 2. What is completed

| Item | Status |
|---|---|
| Chatbot processing flow (intent → facts → retrieval → response → validation) | Done, tested |
| Core NLP/LLM request processing (rule-based intent + entity resolution; optional LLM polish with offline fallback) | Done, tested |
| RAG/retrieval connection (keyword+tag baseline over `saving_tips.md`) | Done, tested |
| FastAPI service (health/chat/intents) + Pydantic schemas | Done, tested |
| Day 15 architecture notes, Day 17 use-case matrix, Day 18 integration flow | Done (docs) |
| Day 19 status/roadmap to Day 30 | Done (docs) |

## 3. What remains (recorded)

1. Push branches and open PRs — blocked (section 4, #1).
2. Budgets & remaining-budget queries (needs budget dataset).
3. Transaction-history listing and month/category comparisons.
4. Embedding/vector retrieval + hybrid rerank (scaffold exists in `rag.py`).
5. Multi-turn conversation memory.
6. Integration with production HisabDo data schema (pending approval).

## 4. Remaining technical blockers (2026-08-21)

| # | Blocker | Impact | Action |
|---|---|---|---|
| 1 | **GitHub push denied (403)** — re-verified today; `AHMEDALIGHORI` not a collaborator on `usmankhalid172/hisabdo-webapp-ai` | Branches/PRs cannot be created remotely; all 10+ commits remain local | Team Leads must add the account (or provide a token with repo scope); exact error in `docs/blockers-and-dependencies.md` |
| 2 | No OpenAI API key in dev environment | Optional LLM-polish path not exercised live | Not blocking; deterministic flow is primary; validate later with a mocked provider test |
| 3 | Keyword+tag retrieval baseline | Lower retrieval quality for paraphrases | Embeddings/rerank planned as Day-30 experiment |
| 4 | Budget dataset absent | Budget use cases blocked | Create/obtain budget dataset |
| 5 | Port 8000 conflict locally | Bind issue during evidence capture | `--port 8010` workaround (documented) |

## 5. GitHub workflow status

- Local branch: `feature/ahmedali-ghori-chatbot-days17-20-completion`
  (from `main`, which contains all chatbot commits).
- Commits: `c07217a` (chatbot impl), `7dc9f75` (docs/matrix), `ff26c3a`
  (403 record), `1fba2b2` (Day 16 features), `5812d64` (lint fixes), plus
  this branch's commits (Day 17-20 docs).
- **PR:** not yet created — push is blocked by 403. Will open PR to `main`
  for Team Lead review as soon as write access is granted.
- No secrets/keys committed: `.env.example` contains a fake placeholder only.

## 6. Next step

Request write access via Team Leads, then `git push -u origin
feature/ahmedali-ghori-chatbot-days17-20-completion` (and the chatbot branch),
open the PR to `main`, and continue the Day-30 roadmap items in
`docs/roadmap-day19.md`.