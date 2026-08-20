# AI Financial Assistant / Chatbot — Implementation Notes

**Branch** : `feature/ahmedali-ghori-ai-chatbot`
**Workstream** : AI Financial Assistant / Chatbot (RAG / NLP)

This document records what was built, which required use cases work today,
which do not yet, and the evidence produced.

---

## 1. What was implemented

A complete, offline-first chatbot pipeline under `src/financial_assistant/` with
a FastAPI service in `src/integration/`, sample data in `data/`, and tests in
`tests/`.

| Module | Responsibility |
| ------ | -------------- |
| `intents.py` | Rule-based intent detection (financial question handling) |
| `transactions.py` | Loads sample data; **backend financial computation** (no LLM maths) |
| `knowledge_base.py` | RAG source corpus loader + chunking (by `##` headings + tags) |
| `retriever.py` | Keyword-overlap + metadata-tag scored retrieval (top-K, min-score) |
| `prompts.py` | Grounded system/user prompts for the optional LLM pass |
| `responders.py` | Deterministic, grounded response builders per intent |
| `response_validator.py` | Empty-response, ungrounded-number, length & scope guards |
| `llm.py` | **Optional** OpenAI-compatible provider; offline fallback |
| `engine.py` | End-to-end flow: intent → facts → retrieval → response → validation |
| `cli.py` | CLI demo (`python -m src.financial_assistant.cli`) |
| `src/integration/app.py` | FastAPI: `GET /health`, `POST /chat`, `POST /intents` |
| `src/integration/schemas.py` | Pydantic request/response models (validation) |

### Assistant flow (per request)
1. Intent detection (rule-based, no model/API needed).
2. Deterministic backend computation of financial facts.
3. RAG retrieval from the saving-tips knowledge base (grounding context).
4. Grounded response builder (never invents figures).
5. Response validation (hallucination/scope guards).
6. Optional LLM polish only if an API key is configured; any failure keeps the
   deterministic answer (soft dependency, not a blocker).

Design follows the team's Day-15 notes (Rameesha's behaviour spec: no
hallucination, clarification on ambiguity, scope control; Farheen's RAG research:
simple hybrid keyword+metadata retrieval, backend calculations, grounded prompts,
graceful fallbacks).

---

## 2. Use-case matrix (what works / what does not)

Reference data: `data/sample_transactions.csv` (June-August 2026 synthetic).
Reference date for relative periods is configurable (`FinancialAssistant(reference_date=...)`).

| # | Required use case | Status | Sample query | Sample response (verified) |
|---|-------------------|--------|--------------|----------------------------|
| 1 | Monthly expense query | ✅ **WORKS** | "How much did I spend this month?" | "Your total spending for August 2026 was PKR 410.35 across 10 transactions." |
| 2 | Monthly expense query | ✅ **WORKS** | "What was my total spending last month?" | "Your total spending for July 2026 was PKR 610.44 across 14 transactions." |
| 3 | Highest spending category | ✅ **WORKS** | "Which category did I spend the most on?" | "Your highest spending category over the available data was Groceries at PKR 583.30." |
| 4 | Spending-summary questions | ✅ **WORKS** | "Give me a spending summary for July" | Bullet breakdown: Groceries 215.75, Dining Out 113.00, Entertainment 103.99, Utilities 89.50, Transport 55.00, Health 33.20 (total 610.44) |
| 5 | Saving-tip requests | ✅ **WORKS** | "How can I save money?" | Returns 2 retrieved KB chunks (retrieval scores > threshold) with a disclaimer |
| 6 | Saving-tip requests | ✅ **WORKS** | "Give me saving tips" | Returns retrieved "Budgeting to save money" chunk text |
| 7 | Out-of-scope question | ✅ safe fallback | "Tell me a joke" | "I am a financial assistant and can only help with …" |
| 8 | Ambiguous (no period) | ✅ clarification | "How much did I spend?" | Asks which time period the user means |

### Not-yet-supported / incomplete (recorded)
| Use case / feature | Status |
|---|---|
| Budgets & remaining-budget queries (Rameesha TC-08/09) | Not implemented. Needs a budget dataset + computation. |
| Transaction history listing ("list my expenses") | Intent not covered; future work. |
| Month-to-month / category comparisons ("compare July and August") | Not implemented. |
| Embedding/vector retrieval + reranking | Recorded as a follow-up in `research/rag-approach.md`; keyword+tag retrieval is the current baseline. |
| Multi-turn conversation history / follow-ups | Not yet stored; current engine is stateless per request. |
| Real user data | Uses synthetic sample data only (`data/sample_transactions.csv`). Integration with production data is future work. |

---

## 3. Evidence produced (this branch)

- **Unit/integration tests**: `python -m unittest discover -s tests -t . -v` → **40/40 OK**.
- **Sample queries + responses**: `python scripts/run_verification.py` (terminal output below).
- **Live API**: `python scripts/run_api_server.py --port 8010`; `curl http://127.0.0.1:8010/health`
  and `curl -X POST .../chat -d '{"question": ...}'`.

Terminal evidence (abridged):

```
Q: How much did I spend this month?
intent: MONTHLY_EXPENSE (0.8) | period: 2026-08
A: Your total spending for August 2026 was PKR 410.35 across 10 transactions.

Q: What is my highest spending category?
intent: HIGHEST_CATEGORY
A: Your highest spending category over the available data was Groceries at PKR 583.30.

Q: Give me saving tips
intent: SAVING_TIP  retrieved: ['Budgeting to save money']
A: Here are some saving tips I found in my knowledge base:
   - Budgeting money: Budgeting means planning your spending ...
   Note: these are general suggestions ... not personalised financial advice.
```

Test results (trailing summary):

```
Ran 40 tests in 0.073s
OK
```

See `docs/blockers-and-dependencies.md` for dependencies and blockers, and
`research/rag-approach.md` for the RAG design rationale.