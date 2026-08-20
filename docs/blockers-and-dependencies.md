# Technical Dependencies & Blockers

Status date: 2026-08-21 · Branches `feature/ahmedali-ghori-ai-chatbot` /
`feature/ahmedali-ghori-chatbot-days17-20-completion`

---

## 1. Technical dependencies

### Required at runtime (core assistant)
- **Python 3.9+ / 3.11** (developed on 3.11).
- **Python standard library only** for `src/financial_assistant/`
  (`csv`, `datetime`, `re`, `dataclasses`, `urllib`). The chatbot flow works
  **fully offline with `pip install` of nothing** for the core pipeline.

### Baseline verified environment
| Component | Version verified |
|---|---|
| Python | 3.11 |
| fastapi | 0.111.0 |
| uvicorn | 0.30.1 |
| pydantic | 2.x (schemas) |

### Optional (non-blocking)
- `OPENAI_API_KEY` → enables the LLM-polish pass. **Not required.** The flow
  falls back to deterministic responses when the key is absent or the call
  fails. See `.env.example` (fake value only).

---

## 2. Repository/team process dependencies
- Branch naming per `CONTRIBUTING.md`: `feature/ahmedali-ghori-ai-chatbot`.
- PR base branch: `main` (Team Lead review required before merge).
- Related team assets this build aligns with (not merged yet on `main` at the
  time of writing):
  - `feature/rameesha-financial-assistant-prompts` (Day-15 prompts/test-case spec).
  - `feature/farheen-fatima-rag-ml-research-day15` (RAG research).

---

## 3. Blockers

| # | Blocker | Impact | Workaround / status |
|---|---------|--------|---------------------|
| 1 | No OpenAI API key available in dev environment | Cannot exercise the live LLM polish path | The deterministic offline pipeline is the primary flow and is fully tested; LLM is an optional enhancement with fallback. Verified `GET /health` reports `llm_available: false`. |
| 2 | Port 8000 already used by another local app (ULTRON AI) during testing | Could not bind default port | Used port 8010 for evidence; `scripts/run_api_server.py` accepts `--port`. |
| 3 | No `pytest` in the dev environment | `pytest`-style tests could not run | Tests are written with stdlib `unittest`; all 40 pass with `python -m unittest discover -s tests -t .` |
| 4 | Production user financial data not yet approved for repo | Cannot validate against real data | Uses synthetic sample data only (`data/sample_transactions.csv`), consistent with `data/README.md`. |
| 5 | RAG is keyword+metadata baseline (no embeddings/reranker) | Retrieval quality for paraphrases/typos is limited | Recorded in `research/rag-approach.md` as the next experiment (embeddings, hybrid search, reranking). |
| 6 | **GitHub push blocked (403)** | Feature branch could not be pushed | Exact error below. Per `CONTRIBUTING.md`, report to Team Leads: the authenticated account must be added as a collaborator on `usmankhalid172/hisabdo-webapp-ai`. |

### GitHub 403 evidence (recorded 2026-08-20, re-verified 2026-08-21)

```
$ git push -u origin feature/ahmedali-ghori-ai-chatbot
remote: Permission to usmankhalid172/hisabdo-webapp-ai.git denied to AHMEDALIGHORI.
fatal: unable to access 'https://github.com/usmankhalid172/hisabdo-webapp-ai.git/':
The requested URL returned error: 403
```

Re-check on 2026-08-21 (push attempt for the same branch) still returned
**403: Permission denied to AHMEDALIGHORI** — the blocker is unresolved; all
chatbot commits (Days 15-20, incl. `feature/ahmedali-ghori-chatbot-days17-20-completion`)
remain local. Day 19/20 status docs record the same blocker.

- GitHub username used by the local credential: `AHMEDALIGHORI`
- `gh auth status`: logged in as `AHMEDALIGHORI` (scopes: gist, read:org, repo, workflow)
- Once write access is granted, run:

```bash
git push -u origin feature/ahmedali-ghori-ai-chatbot
```

---

## 4. Remaining work

1. Budgets & remaining-budget answering (requires a budget dataset).
2. Transaction-history listing and month/category comparisons.
3. Multi-turn conversation memory.
4. Vector/embedding retrieval + hybrid search + rerank (after baseline evaluation).
5. API integration with the HisabDo application backend (real data schema).

---

## 5. Security

- No `.env`, keys, tokens, or private data committed. `.env.example` holds a
  fake key placeholder only.
- The knowledge base and sample transactions are synthetic and safe to commit.