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


def require_internal_token(token: str | None = Security(internal_token_header)) -> None:
    settings = get_settings()
    if token != settings.internal_service_token:
        raise ServiceError(
            "UNAUTHORIZED_SERVICE",
            "Missing or invalid internal service token",
            status_code=401,
        )

from fastapi import Request


def require_authenticated_user(request: Request) -> str:
    """Require a user identity set by trusted authentication middleware."""
    from .errors import ServiceError

    user_id = getattr(request.state, "authenticated_user_id", None)

    if not isinstance(user_id, str) or not user_id.strip():
        raise ServiceError(
            "UNAUTHORIZED_USER",
            "User authentication is required",
            status_code=401,
        )

    return user_id
