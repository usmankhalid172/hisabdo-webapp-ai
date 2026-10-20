"""Shared helpers for identifying questions about Core Services."""
from __future__ import annotations

import re

CORE_SERVICES_QUERY_TERMS = (
    "service", "services", "custom software", "software", "workflow",
    "product foundations", "product development",
    "web development", "web application",
    "web applications", "web app", "web apps", "subscription", "billing",
    "mobile", "mobile app", "mobile application", "android", "ios", "saas",
    "cloud", "azure", "aws", "ai", "ai solution", "ai development",
    "automation", "erp", "devops", "api integration", "application modernization",
    "digital transformation", "ui ux", "ux design",
)


def normalize_service_query_text(value: str) -> str:
    """Normalize punctuation and case for whole-term matching."""
    return re.sub(r"[^\w]+", " ", value.casefold()).strip()


def is_core_services_query(message: str) -> bool:
    """Return whether a message contains a known Core Services topic term."""
    normalized = f" {normalize_service_query_text(message)} "
    return any(
        f" {normalize_service_query_text(term)} " in normalized
        for term in CORE_SERVICES_QUERY_TERMS
    )
