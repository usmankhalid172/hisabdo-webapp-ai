"""Metadata validation for cleaned HisabDo documents."""

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
    errors = []

    for field in REQUIRED_METADATA_FIELDS:
        if field not in document:
            errors.append(f"Missing metadata field: {field}")

    for field in ("title", "section", "category", "language", "product_area"):
        value = document.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Missing or empty metadata field: {field}")

    source_url = document.get("source_url")
    if source_url is not None and source_url != "":
        if not isinstance(source_url, str) or not source_url.startswith(("https://", "http://")):
            errors.append("source_url must be an HTTP or HTTPS URL, or null when unknown")

    updated_date = document.get("updated_date")
    if updated_date is not None and updated_date != "":
        try:
            date.fromisoformat(updated_date)
        except (ValueError, TypeError):
            errors.append("updated_date must use YYYY-MM-DD format, or null when unknown")

    return errors
