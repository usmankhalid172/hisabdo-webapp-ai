# Day 17 — Chatbot POC Applied to Practical HisabDo Use Cases

**Status date:** 2026-08-21
**Branch:** `feature/ahmedali-ghori-ai-chatbot` (continued on
`feature/ahmedali-ghori-chatbot-days17-20-completion`)
**Evidence source:** `python scripts/run_verification.py`,
`python -m unittest discover -s tests -t . -v` (63/63 OK)

---

## 1. What was done

Continued the existing chatbot/RAG implementation from Day 15/16 and ran the
POC against the practical HisabDo financial use cases below. Each use case was
verified through the deterministic offline pipeline (no LLM/API required) and
through the FastAPI `POST /chat` endpoint.

Reference data: `data/sample_transactions.csv` (synthetic, June-August 2026).
Knowledge base: `data/saving_tips.md` (5 chunks, tag metadata).

---

## 2. Verified use cases (currently working)

| # | Use case | Sample query | Verified response |
|---|----------|--------------|-------------------|
| 1 | Monthly expense (this month) | "How much did I spend this month?" | "Your total spending for August 2026 was PKR 410.35 across 10 transactions." |
| 2 | Monthly expense (last month) | "What was my total spending last month?" | "Your total spending for July 2026 was PKR 610.44 across 14 transactions." |
| 3 | Highest spending category | "Which category did I spend the most on?" | "Your highest spending category over the available data was Groceries at PKR 583.30." |
| 4 | Spending summary | "Give me a spending summary for July" | Bullet breakdown per category (Groceries 215.75, Dining Out 113.00, ...) total PKR 610.44 |
| 5 | Saving-tip request | "How can I save money?" | 2 retrieved KB chunks: "Reduce dining-out costs to save", "Cut grocery spending to save" + disclaimer |
| 6 | Saving-tip request (alternate) | "Give me saving tips" | Retrieved "Budgeting to save money" chunk + disclaimer |
| 7 | Out-of-scope question | "Tell me a joke" | Safe fallback: "I am a financial assistant and can only help with questions about your expenses..." |
| 8 | Ambiguous question (no period) | "How much did I spend?" | Clarification request (which time period) |

All of the above also pass as API requests via `POST /chat` (see
`docs/evidence/terminal-and-api-output.txt` for the full evidence trace).

---

## 3. Incomplete / unsupported use cases (recorded)

| Use case / feature | Status | Why / dependency |
|---|---|---|
| Budgets & remaining-budget queries | Not implemented | Needs a budget dataset + computation module; no budget data available yet. |
| Transaction-history listing ("list my expenses") | Intent not covered | Requires paginated history endpoint; future work. |
| Month-to-month / category comparisons ("compare July and August") | Not implemented | Needs comparative aggregation logic; future work. |
| Embedding/vector retrieval + reranking | Baseline only | Keyword+tag retrieval implemented; vector path needs a dependency and evaluation set (see `research/rag-approach.md`). |
| Multi-turn conversation memory / follow-ups | Not implemented | Engine is stateless per request; needs session store. |
| Production user data | Not available | Uses synthetic sample data only; real data integration pending approval. |

---

## 4. Technical dependencies

| Component | Dependency | Status |
|---|---|---|
| Core pipeline (`src/financial_assistant/`) | Python stdlib only | Verified (no pip install needed) |
| API server | fastapi, uvicorn, pydantic (2.x) | Verified in `venv` |
| Tests | stdlib `unittest` | 63/63 pass (pytest not required) |
| Optional LLM polish | `OPENAI_API_KEY` (fake in `.env.example`) | Not required; offline fallback always works |
| Sample data | `data/sample_transactions.csv`, `data/saving_tips.md` | Synthetic, safe to commit |

---

## 5. Blockers

1. **GitHub push blocked (403)** — still active on 2026-08-21; see
   `docs/blockers-and-dependencies.md` (section 3) for exact error and
   required action (account must be added as collaborator).
2. **No OpenAI API key** in dev environment — live LLM path not exercised;
   deterministic pipeline is the primary flow and fully tested.
3. **Port 8000 occupied** by another local app during earlier testing — used
   port 8010; `scripts/run_api_server.py` accepts `--port`.

---

## 6. Evidence produced

- Terminal/API output: `docs/evidence/terminal-and-api-output.txt`
- Test results: 63/63 OK (`Ran 63 tests in 0.209s`)
- Sample queries/responses: section 2 above + verification script output
- Code: `src/financial_assistant/`, `src/integration/`