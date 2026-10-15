
"""Authentication checks for trusted application-to-AI service requests."""

import hmac

from fastapi import Request, Security
from fastapi.security import APIKeyHeader

from .config import get_settings
from .errors import ServiceError

internal_token_header = APIKeyHeader(
    name="X-Internal-Token",
    auto_error=False,
    description="Private token used by the trusted application backend.",
)


def _is_valid_internal_token(token: str | None) -> bool:
    expected = get_settings().internal_service_token

    # Fail closed if the server token is missing or empty.
    return (
        isinstance(expected, str)
        and bool(expected)
        and isinstance(token, str)
        and hmac.compare_digest(token, expected)
    )


def require_internal_token(
    token: str | None = Security(internal_token_header),
) -> None:
    """Reject requests without the configured internal service token."""
    if not _is_valid_internal_token(token):
        raise ServiceError(
            "UNAUTHORIZED_SERVICE",
            "Missing or invalid internal service token",
            status_code=401,
        )


def require_authenticated_user(request: Request) -> str:
    """
    Accept user identity only from a request authenticated as an internal
    application-backend request.

    The application backend must derive this identity from its verified
    login/session. This header is not a substitute for login verification.
    """
    if not _is_valid_internal_token(
        request.headers.get("X-Internal-Token")
    ):
        raise ServiceError(
            "UNAUTHORIZED_SERVICE",
            "Missing or invalid internal service token",
            status_code=401,
        )

    user_id = request.headers.get("X-Authenticated-User-ID")

    if not isinstance(user_id, str) or not user_id.strip():
        raise ServiceError(
            "UNAUTHORIZED_USER",
            "Authenticated user identity is required",
            status_code=401,
        )

    user_id = user_id.strip()
    request.state.authenticated_user_id = user_id
    return user_id
