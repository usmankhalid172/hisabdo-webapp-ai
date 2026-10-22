"""
Service-to-service auth check per Day 15 §5 (mechanism still a placeholder —
see Day 16 continuity plan). Exposed as a FastAPI *dependency* built on a
declared `APIKeyHeader` security scheme, instead of only checking it in raw
middleware.

Why this matters in practice: because it's a declared security scheme,
FastAPI adds it to the OpenAPI spec, and /docs renders a real "Authorize"
button. Click it once, paste the token, and every protected endpoint's
"Try it out" sends the header automatically — no manual header editing.

Release fix: this repository is public, so the placeholder token is public too.
Outside development/test the service refuses to run with the placeholder or a
short token (fail closed), and the comparison is constant-time.
"""
import hmac

from fastapi import Security
from fastapi.security import APIKeyHeader

from .config import get_settings
from .errors import ServiceError

internal_token_header = APIKeyHeader(
    name="X-Internal-Token",
    auto_error=False,
    description="Shared-secret placeholder for service-to-service auth (Day 15 §5). "
                "Value must match INTERNAL_SERVICE_TOKEN in the server's .env.",
)

# Same list as scripts/deployment_configuration_guard.py (the caller-side check).
PLACEHOLDER_TOKENS = {"", "change-me", "change-me-dev-token", "your-token-here", "replace-me"}
MIN_PRODUCTION_TOKEN_LENGTH = 32
NON_PRODUCTION_ENVS = {"development", "dev", "test", "local"}


def _server_token_is_unsafe(settings) -> bool:
    if settings.app_env.strip().lower() in NON_PRODUCTION_ENVS:
        return False
    configured = settings.internal_service_token.strip()
    return configured.lower() in PLACEHOLDER_TOKENS or len(configured) < MIN_PRODUCTION_TOKEN_LENGTH


def require_internal_token(token: str | None = Security(internal_token_header)) -> None:
    settings = get_settings()
    if _server_token_is_unsafe(settings):
        # Fail closed: a misconfigured server answers nobody, rather than anybody who reads the repo.
        raise ServiceError(
            "SERVICE_NOT_CONFIGURED",
            "Service authentication is not configured. Set INTERNAL_SERVICE_TOKEN to a secret of at least "
            f"{MIN_PRODUCTION_TOKEN_LENGTH} characters, or APP_ENV=development for local use.",
            status_code=503,
        )
    # Constant-time comparison, so response timing can't be used to guess the token.
    if token is None or not hmac.compare_digest(token.encode(), settings.internal_service_token.encode()):
        raise ServiceError(
            "UNAUTHORIZED_SERVICE",
            "Missing or invalid internal service token",
            status_code=401,
        )
