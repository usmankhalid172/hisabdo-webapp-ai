
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

from src.financial_assistant.monitoring import (
    start_timer,
    elapsed_ms,
    safe_log_event,
    monitoring_counters,
)

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


def _day1_allowed_document_types(query: str) -> set[str] | None:
    """Separate HisabDo product evidence from general finance evidence."""
    normalized = " ".join(query.lower().split())

    product_patterns = (
        r"\bhisabdo\b",
        r"\bin the app\b",
        r"\bthis app\b",
        r"\bapp feature\b",
        r"\bkhata\b",
        r"\budhar\b",
        r"\bpdf report",
        r"\bexport\b",
        r"\bdownload\b",
        r"\bdashboard\b",
        r"\bcustomer balance",
        r"\bhow do i (use|track|add|record|export|download|view|manage)\b",
        r"\bhow can i (use|track|add|record|export|download|view|manage)\b",
    )
    if any(re.search(pattern, normalized) for pattern in product_patterns):
        return {"product_faq", "product_documentation"}

    finance_patterns = (
        r"\bprofit\b",
        r"\brevenue\b",
        r"\bcash flow\b",
        r"\bwhat is an? expense\b",
        r"\bwhat are expenses\b",
        r"\bfinancial statement\b",
        r"\baccounting\b",
        r"\bpayables?\b",
        r"\breceivables?\b",
    )
    if any(re.search(pattern, normalized) for pattern in finance_patterns):
        return {"finance_faq"}

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
        self.docs_path = Path(docs_path)
        self.model_name = model_name
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

            for field in (
                "url", "source_url", "section",
                "conflict_key", "conflict_value",
            ):
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

    def rebuild_index(self) -> bool:
        """Build a replacement index and retain the old one on failure."""

        started_at = start_timer()

        try:
            candidate = FaqRetriever(
                docs_path=self.docs_path,
                relevance_threshold=self.relevance_threshold,
                model_name=self.model_name,
            )

            if not candidate.documents or candidate.vector_store is None:
                raise ValueError("Replacement index is empty.")

            # Swap only after the replacement index is fully built.
            self.documents, self.vector_store = (
                candidate.documents,
                candidate.vector_store,
            )

            safe_log_event(
                "index_update",
                component="index",
                outcome="success",
                latency_ms=elapsed_ms(started_at),
            )
            return True

        except Exception:
            monitoring_counters.increment("index_update_failures")
            monitoring_counters.increment("errors")

            safe_log_event(
                "index_update",
                component="index",
                outcome="error",
                latency_ms=elapsed_ms(started_at),
                error_category="index_update",
            )
            logger.error(
                "FAQ index update failed; previous index retained."
            )
            return False

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Monitor retrieval while keeping query content out of logs."""

        started_at = start_timer()

        try:
            results = self._retrieve_impl(query, top_k)
            outcome = "success" if results else "fallback"

            if results:
                monitoring_counters.increment("retrieval_success")
            else:
                monitoring_counters.increment("retrieval_empty")

            safe_log_event(
                "retrieval",
                component="retrieval",
                outcome=outcome,
                latency_ms=elapsed_ms(started_at),
                retrieved_source_ids=[
                    item.get("id")
                    for item in results
                    if isinstance(item, dict)
                ],
            )
            return results

        except Exception:
            monitoring_counters.increment("errors")
            safe_log_event(
                "retrieval",
                component="retrieval",
                outcome="error",
                latency_ms=elapsed_ms(started_at),
                error_category="retrieval",
            )
            logger.error("FAQ retrieval failed; details withheld from logs.")
            raise

    def _retrieve_impl(
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

        allowed_types = None
        if self._uses_default_knowledge_base and allowed_ids is None:
            allowed_types = _day1_allowed_document_types(query)

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
            if allowed_ids is not None or allowed_types is not None
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

            if (
                allowed_types is not None
                and metadata.get("type") not in allowed_types
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

            for field in (
                "url", "source_url", "section", "page",
                "conflict_key", "conflict_value",
            ):
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
