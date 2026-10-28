
"""
LangChain-based semantic retrieval for verified HisabDo FAQs
and documentation.

Only verified documents are indexed. Known Day 1 workflow queries
fail closed when no approved, relevant workflow guide is available.
This module does not retrieve live user financial transactions.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger("financial_assistant.faq_rag")

DOCS_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "faq_docs.json"
)

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RELEVANCE_THRESHOLD = 0.40
KB_VERSION = "1.0.0"


def _day1_allowed_document_ids(query: str) -> set[str] | None:
    """
    Return an allowlist for known Day 1 queries.

    An empty set means no verified, workflow-specific document is
    currently approved for that query. None means use normal retrieval.
    """
    normalized = " ".join(query.lower().split())
    compact = normalized.rstrip("?.! ")

    # Product overview.
    if compact in {
        "what can i do with hisabdo",
        "what is hisabdo",
    }:
        return {"faq-001"}

    # The verified export guide is the closest approved source for
    # exporting expenses; it must not be treated as proof of every
    # specific PDF workflow step.
    if (
        "pdf" in normalized
        and ("report" in normalized or "generate" in normalized)
    ):
        return {"faq-005"}

    # These workflows lack confirmed, verified instructions in the
    # current knowledge base. Do not pass unrelated passages as context.
    unsupported_workflow_terms = (
        "categorize an expense",
        "categorize expense",
        "category is wrong",
        "predicted category",
        "total income and expenses",
        "view my total income",
        "add a new customer",
        "record a new expense",
        "record a new expense",
    )

    if any(term in normalized for term in unsupported_workflow_terms):
        return set()

    return None


class FaqRetriever:
    """Retrieve relevant verified FAQs and product documentation."""

    def __init__(
        self,
        docs_path: Path = DOCS_PATH,
        relevance_threshold: float = RELEVANCE_THRESHOLD,
        model_name: str = DEFAULT_MODEL_NAME,
    ):
        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValueError(
                "relevance_threshold must be between 0 and 1."
            )

        self.relevance_threshold = relevance_threshold
        self.documents: list[Document] = []
        self.vector_store = None

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

            # Never ground answers in unverified content.
            if item.get("verified") is not True:
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
                "No verified knowledge-base documents are available."
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Return relevant verified documents with source attribution."""

        if not isinstance(query, str) or not query.strip():
            return []

        if top_k <= 0 or self.vector_store is None:
            return []

        allowed_ids = _day1_allowed_document_ids(query)

        # Fail closed for known workflows with no approved guide.
        if allowed_ids == set():
            return []

        # Search all indexed documents when an allowlist is needed,
        # otherwise retain the caller's requested top-k behavior.
        search_k = (
            len(self.documents)
            if allowed_ids is not None
            else top_k
        )

        matches = self.vector_store.similarity_search_with_score(
            query.strip(),
            k=search_k,
        )

        results = []

        for document, score in matches:
            metadata = document.metadata

            if (
                allowed_ids is not None
                and metadata["id"] not in allowed_ids
            ):
                continue

            score = float(score)

            if score < self.relevance_threshold:
                continue

            results.append({
                "id": metadata["id"],
                "title": metadata["title"],
                "text": document.page_content,
                "source": metadata["source"],
                "type": metadata["type"],
                "version": metadata["version"],
                "verified": metadata["verified"],
                "score": round(score, 4),
                "page": metadata.get("page"),
            })

            if len(results) >= top_k:
                break

        return results


@lru_cache(maxsize=1)
def get_retriever() -> FaqRetriever:
    """Return a cached retriever instance."""
    return FaqRetriever()
