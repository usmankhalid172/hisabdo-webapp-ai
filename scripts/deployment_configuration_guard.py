"""
Deployment configuration guardrail.

Purpose:
    Check required AI-service deployment configuration before startup and
    print clear, non-sensitive warnings for missing, placeholder, or invalid
    settings.

This script does not print secrets and does not make network calls.
"""

from __future__ import annotations

import os
import sys


PLACEHOLDER_TOKENS = {
    "",
    "change-me",
    "change-me-dev-token",
    "your-token-here",
    "replace-me",
}


def _configured(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def check_configuration() -> tuple[bool, list[str], list[str]]:
    """Return (ready, warnings, checks) for the current environment."""
    warnings: list[str] = []
    checks: list[str] = []

    base_url = os.getenv("AI_SERVICE_BASE_URL")
    token = os.getenv("AI_SERVICE_INTERNAL_TOKEN")
    timeout_raw = os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "15")

    ready = True

    if _configured(base_url):
        checks.append("[OK] AI_SERVICE_BASE_URL is configured.")
    else:
        warnings.append(
            "[WARNING] AI_SERVICE_BASE_URL is missing. "
            "AI-dependent features may fail at runtime."
        )
        ready = False

    if not _configured(token):
        warnings.append(
            "[WARNING] AI_SERVICE_INTERNAL_TOKEN is missing. "
            "Authenticated AI calls will fail."
        )
        ready = False
    elif token.strip().lower() in PLACEHOLDER_TOKENS:
        warnings.append(
            "[WARNING] AI_SERVICE_INTERNAL_TOKEN is using a development "
            "placeholder. Configure a deployment secret before production."
        )
        ready = False
    else:
        checks.append("[OK] AI_SERVICE_INTERNAL_TOKEN is configured.")

    try:
        timeout = float(timeout_raw)
        if timeout <= 0:
            raise ValueError
        checks.append(
            f"[OK] AI_SERVICE_TIMEOUT_SECONDS is valid ({timeout:g}s)."
        )
    except (TypeError, ValueError):
        warnings.append(
            "[WARNING] AI_SERVICE_TIMEOUT_SECONDS must be a positive number."
        )
        ready = False

    return ready, warnings, checks


def main() -> int:
    """Print configuration status without exposing secret values."""
    ready, warnings, checks = check_configuration()

    print("Deployment configuration guardrail")
    print("----------------------------------")

    for message in checks:
        print(message)

    for warning in warnings:
        print(warning)

    if ready:
        print("[READY] Required AI service configuration is present.")
        return 0

    print(
        "[NOT READY] Review the warnings above before relying on "
        "AI-dependent features."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
