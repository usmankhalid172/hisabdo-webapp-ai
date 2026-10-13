"""
Service-to-service auth check per Day 15 §5 (mechanism still a placeholder —
see Day 16 continuity plan). Exposed as a FastAPI *dependency* built on a
declared `APIKeyHeader` security scheme, instead of only checking it in raw
middleware.

Why this matters in practice: because it's a declared security scheme,
FastAPI adds it to the OpenAPI spec, and /docs renders a real "Authorize"
button. Click it once, paste the token, and every protected endpoint's
"Try it out" sends the header automatically — no manual header editing.
"""
from fastapi import Header, Security
from fastapi.security import APIKeyHeader

from .config import get_settings
from .errors import ServiceError

internal_token_header = APIKeyHeader(
    name="X-Internal-Token",
    auto_error=False,
    description="Shared-secret placeholder for service-to-service auth (Day 15 §5). "
                "Value must match INTERNAL_SERVICE_TOKEN in the server's .env.",
)


def require_internal_token(token: str | None = Security(internal_token_header)) -> None:
    settings = get_settings()
    if token != settings.internal_service_token:
        raise ServiceError(
            "UNAUTHORIZED_SERVICE",
            "Missing or invalid internal service token",
            status_code=401,
        )


def require_customer_access(
    requested_user_id: str,
    authenticated_user_id: str | None,
) -> None:
    """Enforce account ownership using an identity asserted by a trusted gateway."""
    if not authenticated_user_id or not authenticated_user_id.strip():
        raise ServiceError(
            "UNAUTHENTICATED_CUSTOMER",
            "Authenticated customer identity is required for financial data",
            status_code=401,
        )

    if requested_user_id.strip() != authenticated_user_id.strip():
        raise ServiceError(
            "CUSTOMER_ACCESS_DENIED",
            "The requested account does not belong to the authenticated customer",
            status_code=403,
        )
