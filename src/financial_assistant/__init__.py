"""AI Financial Assistant / Chatbot package.

Modules:
- intents: rule-based financial intent detection
- transactions: safe loading and backend financial computation
- knowledge_base: RAG source document corpus
- retriever: scored retrieval with metadata filtering
- prompts: grounded system/user prompt builders
- responders: build grounded, validated responses per intent
- llm: optional pluggable LLM provider with offline fallback
- engine: end-to-end assistant orchestration
- cli: interactive command-line demo
"""
from . import (
    intents,
    transactions,
    knowledge_base,
    retriever,
    prompts,
    llm,
    responders,
    response_validator,
    engine,
)

__all__ = [
    "intents",
    "transactions",
    "knowledge_base",
    "retriever",
    "prompts",
    "llm",
    "responders",
    "response_validator",
    "engine",
]