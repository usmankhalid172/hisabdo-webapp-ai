"""RAG / knowledge-base package for the HisabDo AI assistant.

Contains the retrieval primitives used across the assistant:

- :mod:`faq` - the chatbot's FAQ/product-docs ``FaqRetriever`` (TF-IDF over
  ``data/faq_docs.json``), plus the cached ``get_retriever()`` factory.
- :mod:`knowledge_base` - ``load_knowledge_base`` loader for JSON corpora.
- :mod:`retriever` - the ``FinancialRetriever`` prototype (TF-IDF over a
  knowledge-base of question/answer documents).

Everything is re-exported here so callers can use either a single flat
import (``from src.financial_assistant.rag import get_retriever``) or a
module-qualified import (``from src.financial_assistant.rag.faq import ...``).

Task 26 fixed a module-vs-package name collision (there was once both a
``rag.py`` *and* a ``rag/`` *package*), which made the chatbot endpoint fail
to import. The package is now the single canonical ``rag`` namespace.
"""

from .faq import DOCS_PATH, RELEVANCE_THRESHOLD, FaqRetriever, get_retriever
from .knowledge_base import load_knowledge_base
from .retriever import FinancialRetriever

__all__ = [
    "DOCS_PATH",
    "RELEVANCE_THRESHOLD",
    "FaqRetriever",
    "get_retriever",
    "load_knowledge_base",
    "FinancialRetriever",
]
