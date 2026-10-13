import json
from pathlib import Path
from typing import Dict, List, Any


KB_VERSION = "1.0.0"


def load_knowledge_base(file_path: str) -> List[Dict]:
    """Load and validate knowledge-base documents from a JSON file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Knowledge base not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Knowledge base must contain a JSON list.")

    validated_documents = []

    for index, document in enumerate(data):
        if not isinstance(document, dict):
            raise ValueError(
                f"Document at index {index} must be a JSON object."
            )

        question = document.get("question", "")
        answer = document.get("answer", "")

        if not isinstance(question, str) or not isinstance(answer, str):
            raise ValueError(
                f"Document at index {index} must have string question "
                "and answer fields."
            )

        if not question.strip() or not answer.strip():
            raise ValueError(
                f"Document at index {index} must have a non-empty "
                "question and answer."
            )

        document_type = document.get("type", "faq")

        if document_type not in ("faq", "product_documentation"):
            raise ValueError(
                f"Document at index {index} has an unsupported type: "
                f"{document_type}"
            )

        verified = document.get("verified", False)

        if not isinstance(verified, bool):
            raise ValueError(
                f"Document at index {index} must use a boolean "
                "'verified' field."
            )

        validated_document = dict(document)
        validated_document["type"] = document_type
        validated_document["verified"] = verified
        validated_document["version"] = document.get(
            "version", KB_VERSION
        )

        validated_documents.append(validated_document)

    return validated_documents


def get_knowledge_base_metadata(
    documents: List[Dict],
) -> Dict[str, Any]:
    """Return version and verification statistics for the knowledge base."""
    return {
        "version": KB_VERSION,
        "total_documents": len(documents),
        "verified_documents": sum(
            1 for doc in documents if doc.get("verified") is True
        ),
        "faq_documents": sum(
            1 for doc in documents if doc.get("type") == "faq"
        ),
        "product_documentation_documents": sum(
            1
            for doc in documents
            if doc.get("type") == "product_documentation"
        ),
    }