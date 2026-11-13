"""Shared helpers for identifying website section questions."""
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

CAREERS_QUERY_TERMS = (
    "career", "careers", "job", "jobs", "job opening", "job openings",
    "vacancy", "vacancies", "hiring", "recruitment", "internship",
    "internships", "apply for", "application status", "application received",
    "received my application", "my application", "applicant", "employment",
    "job offer", "position",
    "positions", "opening", "openings", "role", "roles", "resume", "cv",
    "interview", "salary", "compensation", "eligibility", "benefits",
)

PORTFOLIO_QUERY_TERMS = (
    "portfolio", "case study", "case studies", "our work", "past project",
    "past projects", "project outcome", "project outcomes", "project result",
    "project results", "flagship product", "technology stack", "tech stack",
    "built with", "screenshots",
)

HISABDO_PROJECT_DETAIL_TERMS = (
    "technology", "technologies", "stack", "outcome", "outcomes", "challenge",
    "approach", "built with", "screenshots", "flagship", "result", "results",
    "measurable",
)

PERSONAL_APPLICATION_STATUS_TERMS = (
    "my application", "application status", "application received",
    "received my application", "check my application", "my interview status",
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


def is_careers_query(message: str) -> bool:
    """Identify recruitment questions for the XICTEK Careers source route."""
    normalized = f" {normalize_service_query_text(message)} "
    return any(
        f" {normalize_service_query_text(term)} " in normalized
        for term in CAREERS_QUERY_TERMS
    )


def is_portfolio_query(message: str) -> bool:
    """Identify portfolio and project-summary questions for the portfolio route."""
    normalized = f" {normalize_service_query_text(message)} "
    if any(
        f" {normalize_service_query_text(term)} " in normalized
        for term in PORTFOLIO_QUERY_TERMS
    ):
        return True
    has_hisabdo = " hisabdo " in normalized
    asks_project_detail = any(
        f" {normalize_service_query_text(term)} " in normalized
        for term in HISABDO_PROJECT_DETAIL_TERMS
    )
    return has_hisabdo and asks_project_detail


def is_personal_application_status_query(message: str) -> bool:
    """Identify private application-status requests public website content cannot answer."""
    normalized = f" {normalize_service_query_text(message)} "
    return any(
        f" {normalize_service_query_text(term)} " in normalized
        for term in PERSONAL_APPLICATION_STATUS_TERMS
    )
