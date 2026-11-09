"""Metadata validation for standardized HisabDo knowledge records."""

from datetime import date
from typing import Any

REQUIRED_METADATA_FIELDS = (
    "title",
    "section",
    "category",
    "source_url",
    "language",
    "updated_date",
    "product_area",
)


def validate_metadata(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not isinstance(document, dict):
        return ["Document must be a dictionary"]

    for field in REQUIRED_METADATA_FIELDS:
        if field not in document:
            errors.append(f"Missing metadata field: {field}")

    for field in (
        "title",
        "section",
        "category",
        "language",
        "product_area",
    ):
        value = document.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Missing or empty metadata field: {field}")

    source_url = document.get("source_url")
    if source_url is not None and source_url != "":
        if (
            not isinstance(source_url, str)
            or not source_url.startswith(("https://", "http://"))
        ):
            errors.append("source_url must be an HTTP or HTTPS URL, or null")

    updated_date = document.get("updated_date")
    if updated_date is not None and updated_date != "":
        try:
            parsed_date = date.fromisoformat(updated_date)
            if parsed_date.isoformat() != updated_date:
                errors.append("updated_date must use YYYY-MM-DD format")
        except (ValueError, TypeError):
            errors.append("updated_date must use YYYY-MM-DD format or null")

    return errors


def validate_batch(documents: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []

    if not isinstance(documents, list):
        return ["Batch must be a list"]

    seen_ids: set[str] = set()

    for index, document in enumerate(documents):
        prefix = f"Record {index + 1}"

        if not isinstance(document, dict):
            errors.append(f"{prefix}: Document must be a dictionary")
            continue

        errors.extend(
            f"{prefix}: {error}"
            for error in validate_metadata(document)
        )

        record_id = document.get("id") or document.get("chunk_id")

        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"{prefix}: Missing record ID")
        elif record_id in seen_ids:
            errors.append(f"{prefix}: Duplicate record ID: {record_id}")
        else:
            seen_ids.add(record_id)

        has_faq_content = bool(
            isinstance(document.get("text"), str)
            and document["text"].strip()
        )

        has_financial_content = bool(
            isinstance(document.get("question"), str)
            and document["question"].strip()
            and isinstance(document.get("answer"), str)
            and document["answer"].strip()
        )

        has_chunk_content = bool(
            isinstance(document.get("text"), str)
            and document["text"].strip()
            and document.get("document_id")
        )

        if not (
            has_faq_content
            or has_financial_content
            or has_chunk_content
        ):
            errors.append(f"{prefix}: Missing valid knowledge content")

    return errors