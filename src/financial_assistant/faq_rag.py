
"""
LangChain-based semantic retrieval for verified HisabDo FAQs
and documentation.

Only verified and safe documents are indexed. Unsupported workflow
queries fail closed. This module does not retrieve live transactions.
"""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from src.financial_assistant.guardrails import (
    get_input_guardrail,
    is_safe_knowledge_content,
    MAX_MESSAGE_CHARS,
)

logger = logging.getLogger("financial_assistant.faq_rag")

DOCS_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "faq_docs.json"
)

DEFAULT_DOCS_PATH = DOCS_PATH

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RELEVANCE_THRESHOLD = 0.40
KB_VERSION = "1.0.0"
MAX_RETRIEVAL_TOP_K = 10


def _is_payable_receivable_query(query: str) -> bool:
    """Identify questions about payable and receivable concepts."""
    normalized = " ".join(query.lower().split())

    patterns = (
        r"\bpayables?\b",
        r"\breceivables?\b",
        r"\baccounts payable\b",
        r"\baccounts receivable\b",
        r"\bmoney owed\b",
        r"\bamount owed\b",
        r"\bwhat i owe\b",
        r"\bwhat does .* owe\b",
        r"\bowe and owed\b",
        r"\bpayable and receivable\b",
        r"\breceivable and payable\b",
        r"\bcustomer owes\b",
        r"\bcustomer balance\b",
        r"\budhar\b",
        r"\bkhata\b",
    )

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


def _day1_allowed_document_ids(query: str) -> set[str] | None:
    """Return an allowlist for known Day 1 queries."""
    normalized = " ".join(query.lower().split())
    compact = normalized.rstrip("?.! ")

    if compact in {
        "what can i do with hisabdo",
        "what is hisabdo",
    }:
        return {"faq-001"}

    if (
        "pdf" in normalized
        and ("report" in normalized or "generate" in normalized)
    ):
        return {"faq-005"}

    unsupported_workflow_terms = (
        "categorize an expense",
        "categorize expense",
        "category is wrong",
        "predicted category",
        "total income and expenses",
        "view my total income",
        "add a new customer",
        "record a new expense",
    )

    if any(term in normalized for term in unsupported_workflow_terms):
        return set()

    return None


class FaqRetriever:
    """Retrieve relevant verified and safe FAQ documents."""

    def __init__(
        self,
        docs_path: Path = DOCS_PATH,
        relevance_threshold: float = RELEVANCE_THRESHOLD,
        model_name: str = DEFAULT_MODEL_NAME,
    ):
        if not isinstance(relevance_threshold, (int, float)):
            raise ValueError("relevance_threshold must be numeric.")

        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValueError(
                "relevance_threshold must be between 0 and 1."
            )

        self.relevance_threshold = relevance_threshold
        self.documents: list[Document] = []
        self.vector_store = None

        self._uses_default_knowledge_base = (
            Path(docs_path).resolve() == DEFAULT_DOCS_PATH.resolve()
        )

        if not docs_path.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {docs_path}"
            )

        with docs_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Knowledge base must contain a JSON list.")

        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Knowledge-base entry {index} must be an object."
                )

            title = item.get("title", "")
            content = item.get("text", "")

            if not isinstance(title, str) or not isinstance(content, str):
                raise ValueError(
                    f"Knowledge-base entry {index} has invalid text fields."
                )

            if not title.strip() or not content.strip():
                continue

            if item.get("verified") is not True:
                continue

            # Reject malicious instructions and sensitive content.
            if not is_safe_knowledge_content(f"{title}\n{content}"):
                logger.warning(
                    "Unsafe knowledge-base document skipped: index=%s",
                    index,
                )
                continue

            metadata = {
                "id": str(item.get("id", f"document-{index + 1}")),
                "title": title,
                "source": str(
                    item.get("source", "HisabDo Knowledge Base")
                ),
                "type": str(item.get("type", "faq")),
                "version": str(item.get("version", KB_VERSION)),
                "verified": True,
            }

            for field in ("url", "source_url", "section"):
                value = item.get(field)
                if isinstance(value, str) and value.strip():
                    metadata[field] = value.strip()

            if item.get("page") is not None:
                metadata["page"] = item["page"]

            self.documents.append(
                Document(
                    page_content=f"{title}\n{content}",
                    metadata=metadata,
                )
            )

        if self.documents:
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            self.vector_store = InMemoryVectorStore.from_documents(
                documents=self.documents,
                embedding=embeddings,
            )
        else:
            logger.warning(
                "No verified safe knowledge-base documents are available."
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Return relevant verified and safe documents with attribution."""

        if not isinstance(query, str) or not query.strip():
            return []

        # Enforce query length before retrieval.
        if len(query) > MAX_MESSAGE_CHARS:
            return []

        # Validate top_k type and supported range.
        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or not 1 <= top_k <= MAX_RETRIEVAL_TOP_K
        ):
            return []

        if self.vector_store is None:
            return []

        # Block prompt injection, unsafe requests and out-of-scope queries.
        guardrail_reason = get_input_guardrail(query)

        if guardrail_reason is not None:
            logger.warning(
                "FAQ retrieval blocked by input guardrail: %s",
                guardrail_reason,
            )
            return []

        allowed_ids = _day1_allowed_document_ids(query)

        targeted_udhar_query = (
            self._uses_default_knowledge_base
            and _is_payable_receivable_query(query)
        )

        if targeted_udhar_query:
            allowed_ids = {"faq-udhar-guidance"}

        if (
            self._uses_default_knowledge_base
            and allowed_ids == set()
        ):
            return []

        if (
            not self._uses_default_knowledge_base
            and allowed_ids == set()
        ):
            allowed_ids = None

        search_k = (
            len(self.documents)
            if allowed_ids is not None
            else top_k
        )

        matches = self.vector_store.similarity_search_with_score(
            query.strip(),
            k=search_k,
        )

        results: list[dict[str, Any]] = []

        for document, score in matches:
            metadata = document.metadata

            if (
                allowed_ids is not None
                and metadata["id"] not in allowed_ids
            ):
                continue

            # Revalidate retrieved content before returning it.
            if not is_safe_knowledge_content(document.page_content):
                logger.warning(
                    "Unsafe retrieved document rejected: %s",
                    metadata.get("id", "unknown"),
                )
                continue

            score = float(score)

            if (
                score < self.relevance_threshold
                and not (
                    targeted_udhar_query
                    and metadata["id"] == "faq-udhar-guidance"
                )
            ):
                continue

            result = {
                "id": metadata["id"],
                "title": metadata["title"],
                "text": document.page_content,
                "source": metadata["source"],
                "type": metadata["type"],
                "version": metadata["version"],
                "verified": metadata["verified"],
                "score": round(score, 4),
            }

            for field in ("url", "source_url", "section", "page"):
                value = metadata.get(field)
                if value is not None:
                    result[field] = value

            results.append(result)

            if len(results) >= top_k:
                break

        return results


@lru_cache(maxsize=1)
def get_retriever() -> FaqRetriever:
    """Return a cached retriever instance."""
    return FaqRetriever()
