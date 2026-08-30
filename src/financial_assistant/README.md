# Financial Assistant / Chatbot

Implementation lives in module folders matching `src/financial_assistant/`:

| Module | Purpose |
| ------ | ------- |
| `intents.py` | Rule-based financial intent detection |
| `transactions.py` | Sample data loading + backend financial computation |
| `knowledge_base.py` | RAG corpus loader + chunking (saving-tips KB) |
| `retriever.py` | Scored retrieval (keyword overlap + metadata tags) |
| `prompts.py` | Grounded system/user prompt builders |
| `responders.py` | Deterministic grounded response builders per intent |
| `response_validator.py` | Empty / ungrounded-number / scope validation guards |
| `llm.py` | Optional LLM provider (OpenAI-compatible) with offline fallback |
| `engine.py` | End-to-end assistant orchestration (`FinancialAssistant.ask`) |
| `cli.py` | CLI demo / sample-query runner |

## Run

```bash
# tests
python -m unittest discover -s tests -t . -v

# terminal evidence / sample queries
python scripts/run_verification.py

# interactive CLI
python -m src.financial_assistant.cli --interactive

# optional live API server (default port 8000, override with --port)
python scripts/run_api_server.py --port 8010
```

## Status

Supported intents: `MONTHLY_EXPENSE`, `HIGHEST_CATEGORY`, `SPENDING_SUMMARY`,
`SAVING_TIP` (plus greeting/help/ambiguous/unsupported handling).

The core flow is deterministic and runs offline (stdlib only). An optional
LLM polish step activates only when `OPENAI_API_KEY` is set; failures always
fall back to the deterministic response.

See `docs/chatbot-implementation.md`, `docs/blockers-and-dependencies.md`, and
`research/rag-approach.md`.
