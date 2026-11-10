"""Authentication: work out WHO is calling, from a credential the caller can't forge.

The user's identity always comes from the credential. Nothing in the request
body or query string can choose whose data is read.

    AUTH_MODE=supabase  Authorization: Bearer <Supabase access token>
                        Checked: signature (HS256 only), expiry, audience,
                        role "authenticated", not an anonymous session, and the
                        token's user ID must be linked to a user in our database.
    AUTH_MODE=dev       X-User-Id: U-001   (no password - local development only;
                        Settings.validate() refuses it in production)
    anything else       401 for every request
"""

from __future__ import annotations

from uuid import UUID

import jwt

from .config import Settings
from .models import User
from .repository import RecordNotFound, Repository


class AuthError(Exception):
    """Authentication failed. The message is safe to show to the caller."""


def authenticate(
    settings: Settings, repo: Repository, authorization: str | None, x_user_id: str | None
) -> User:
    if settings.auth_mode == "supabase":
        # X-User-Id is deliberately ignored here, even if present.
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("Missing bearer token.")
        auth_id = _verify_supabase_token(token.strip(), settings)
        try:
            return repo.get_user_by_auth_id(auth_id)
        except RecordNotFound:
            # A valid login that isn't linked to any business yet.
            raise AuthError("This account has no access to HisabDo data.") from None

    if settings.auth_mode == "dev" and settings.allow_dev_auth and not settings.is_production:
        if not x_user_id:
            raise AuthError("Missing X-User-Id header (dev auth).")
        try:
            return repo.get_user(x_user_id)
        except RecordNotFound:
            raise AuthError("Unknown user.") from None

    raise AuthError("Authentication is not configured.")


def _verify_supabase_token(token: str, settings: Settings) -> str:
    try:
        claims = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],  # fixed list: blocks "alg: none" and algorithm switching
            audience=settings.supabase_jwt_audience,
            options={"require": ["exp", "sub", "aud"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("Session expired. Please sign in again.") from None
    except jwt.PyJWTError:
        raise AuthError("Invalid authentication token.") from None
    # Rejects the public "anon" key, service-role keys, and anonymous sign-ins.
    if claims.get("role") != "authenticated" or claims.get("is_anonymous"):
        raise AuthError("Invalid authentication token.")
    try:
        return str(UUID(str(claims["sub"])))
    except (ValueError, TypeError):
        raise AuthError("Invalid authentication token.") from None
