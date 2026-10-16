"""Offline evaluation of Core Services query coverage and answer formatting.

Run from the repository root with:

    python scripts/evaluate_core_services_formatting.py

The cases use deterministic, source-grounded answer fixtures. This evaluates
query routing and the post-processing contract; it does not call an LLM or
measure live retrieval quality.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.xictek_website_assistant.formatting import format_core_services_output
from src.xictek_website_assistant.service_queries import is_core_services_query


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    query: str
    model_output: str
    expected_items: tuple[str, ...]


CASES = (
    EvaluationCase("custom software scope", "What custom software services do you offer?", "XICTEK provides workflow discovery, web development, mobile development, business systems, integrations, testing, deployment, and support.", ("workflow discovery", "web development", "mobile development", "business systems", "integrations", "testing", "deployment", "support")),
    EvaluationCase("web application types", "What kinds of web applications can you build?", "Business portals; SaaS interfaces; dashboards; customer platforms; internal tools; product websites.", ("Business portals", "SaaS interfaces", "dashboards", "customer platforms", "internal tools", "product websites")),
    EvaluationCase("web technology stack", "Which technologies do you use for web development?", "React, Next.js, TypeScript, PostgreSQL, and cloud services.", ("React", "Next.js", "TypeScript", "PostgreSQL", "cloud services")),
    EvaluationCase("web development stages", "What are the stages of your web development process?", "Stages include discovery, architecture, implementation, testing, deployment, and ongoing improvements.", ("discovery", "architecture", "implementation", "testing", "deployment", "ongoing improvements")),
    EvaluationCase("mobile frameworks", "Which frameworks do you use for mobile app development?", "1. Flutter\n2. React Native", ("Flutter", "React Native")),
    EvaluationCase("mobile capabilities", "What mobile app capabilities do you provide?", "Offline-first workflows; local storage; synchronization rules; push notifications; related APIs.", ("Offline-first workflows", "local storage", "synchronization rules", "push notifications", "related APIs")),
    EvaluationCase("mobile integrations", "What can a mobile app integrate with?", "Secure authentication, APIs, file storage, payments, analytics, and administrative tools.", ("Secure authentication", "APIs", "file storage", "payments", "analytics", "administrative tools")),
    EvaluationCase("cloud platforms", "Which cloud platforms do you support?", "Azure and AWS.", ("Azure", "AWS")),
    EvaluationCase("Azure services", "What Azure development services are available?", "Azure application architecture; App Services; Functions; deployment workflows; databases; integrations; modernization planning.", ("Azure application architecture", "App Services", "Functions", "deployment workflows", "databases", "integrations", "modernization planning")),
    EvaluationCase("cloud operating baseline", "What is included in a cloud operating baseline?", "Logging, alerts, backups, access controls, and cost visibility.", ("Logging", "alerts", "backups", "access controls", "cost visibility")),
    EvaluationCase("AI services", "What AI services does XICTEK provide?", "LLM and OpenAI integrations; AI assistants and chatbots; document processing and extraction; workflow automation and evaluation.", ("LLM and OpenAI integrations", "AI assistants and chatbots", "document processing and extraction", "workflow automation and evaluation")),
    EvaluationCase("AI solution types", "What types of AI solutions can you build?", "AI assistants; document extraction; knowledge search; customer support workflows; content tools; automation connected to existing business systems.", ("AI assistants", "document extraction", "knowledge search", "customer support workflows", "content tools", "automation connected to existing business systems")),
    EvaluationCase("AI production considerations", "What do you consider when putting AI features into production?", "Authentication, permissions, data boundaries, fallback behavior, logging, evaluation, and a clear user experience.", ("Authentication", "permissions", "data boundaries", "fallback behavior", "logging", "evaluation", "a clear user experience")),
    EvaluationCase("ERP services", "What ERP services do you offer?", "Custom ERP modules and workflows; inventory and customer records; approvals and role-based access; reports and operational dashboards.", ("Custom ERP modules and workflows", "inventory and customer records", "approvals and role-based access", "reports and operational dashboards")),
    EvaluationCase("ERP integration", "What records can you integrate into an ERP?", "Inventory, customer records, finance-related records, approvals, and reporting.", ("Inventory", "customer records", "finance-related records", "approvals", "reporting")),
    EvaluationCase("SaaS architecture", "What architecture features do your SaaS solutions include?", "Multi-tenant architecture; tenant isolation; authentication; authorization; audit trails; backups; observability.", ("Multi-tenant architecture", "tenant isolation", "authentication", "authorization", "audit trails", "backups", "observability")),
    EvaluationCase("SaaS billing", "What subscription and billing capabilities do you support?", "Subscription flows; billing events; usage limits.", ("Subscription flows", "billing events", "usage limits")),
    EvaluationCase("SaaS analytics", "What analytics and reporting do you offer for SaaS?", "Analytics and operational dashboards; product events connected to business reporting.", ("Analytics and operational dashboards", "product events connected to business reporting")),
)


def _bullet_items(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for line in text.splitlines()
        if (match := re.match(r"^\s*-\s+(.+?)\s*$", line))
    ]


def _evaluate_case(case: EvaluationCase) -> list[str]:
    failures: list[str] = []
    if not is_core_services_query(case.query):
        failures.append("query was not classified as Core Services")

    formatted = format_core_services_output(case.model_output)
    actual_items = _bullet_items(formatted)
    if len(actual_items) < 2:
        failures.append("multi-service response did not become at least two Markdown bullets")
    if actual_items != list(case.expected_items):
        failures.append(f"items differ; expected {list(case.expected_items)!r}, got {actual_items!r}")
    if len({item.casefold() for item in actual_items}) != len(actual_items):
        failures.append("duplicate bullet items were retained")
    long_items = [item for item in actual_items if len(item.split()) > 20]
    if long_items:
        failures.append(f"item exceeds concise-output limit (20 words): {long_items!r}")
    return failures


def main() -> int:
    passed = 0
    failed = 0
    for case in CASES:
        failures = _evaluate_case(case)
        if failures:
            failed += 1
            print(f"FAIL  {case.name}")
            for failure in failures:
                print(f"      - {failure}")
        else:
            passed += 1
            print(f"PASS  {case.name}")

    # Guard the formatter's scope: ordinary prose and a single service stay prose.
    preservation_checks = (
        ("single item", "XICTEK offers Flutter.", "XICTEK offers Flutter."),
        ("ordinary prose", "XICTEK supports teams throughout delivery.", "XICTEK supports teams throughout delivery."),
    )
    for name, source, expected in preservation_checks:
        actual = format_core_services_output(source)
        if actual != expected:
            failed += 1
            print(f"FAIL  preservation: {name} (got {actual!r})")
        else:
            passed += 1
            print(f"PASS  preservation: {name}")

    total = passed + failed
    print(f"\nResult: {passed}/{total} checks passed; {failed} failed.")
    print(f"Cases: {len(CASES)} Core Services query variations plus 2 preservation checks.")
    print("Scope: deterministic fixtures; no LLM/network call and no live RAG accuracy claim.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
