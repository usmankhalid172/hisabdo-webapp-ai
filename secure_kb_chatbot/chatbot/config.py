"""Settings, read once from environment variables (.env is never committed).

Secure by default: with nothing configured, authentication is off (every
request gets 401), demo data is hidden, and the knowledge base is unused.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

MIN_JWT_SECRET_LENGTH = 32


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # --- authentication -------------------------------------------------------------
    # "supabase": Authorization: Bearer <Supabase access token>   (production)
    # "dev":      X-User-Id header, no password                    (your laptop only)
    # anything else: every request is rejected with 401
    auth_mode: str = "disabled"
    # Dev mode needs BOTH this flag and a non-production APP_ENV, so one wrong
    # variable on a server can't switch authentication off.
    allow_dev_auth: bool = False
    app_env: str = "production"
    supabase_jwt_secret: str = field(default="", repr=False)  # never printed or logged
    supabase_jwt_audience: str = "authenticated"

    # --- data ---------------------------------------------------------------------------
    allow_demo_data: bool = False  # businesses flagged is_demo are blocked unless this is on
    reporting_timezone: str = "Asia/Karachi"  # "today" and report periods use this, not the server clock
    max_period_days: int = 366

    # --- knowledge base retrieval -----------------------------------------------------
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768
    kb_threshold: float = 0.60  # minimum cosine similarity; calibrate with scripts/calibrate_threshold.py
    kb_top_k: int = 4
    note_threshold: float = 0.55

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            auth_mode=os.getenv("AUTH_MODE", "disabled").strip().lower(),
            allow_dev_auth=_flag("ALLOW_DEV_AUTH"),
            app_env=os.getenv("APP_ENV", "production").strip().lower(),
            supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", "").strip(),
            supabase_jwt_audience=os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip(),
            allow_demo_data=_flag("ALLOW_DEMO_DATA"),
            reporting_timezone=os.getenv("REPORTING_TIMEZONE", "Asia/Karachi").strip(),
            max_period_days=int(os.getenv("MAX_PERIOD_DAYS", "366")),
            embedding_model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip(),
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "768")),
            kb_threshold=float(os.getenv("KB_THRESHOLD", "0.60")),
            kb_top_k=int(os.getenv("KB_TOP_K", "4")),
            note_threshold=float(os.getenv("NOTE_THRESHOLD", "0.55")),
        )

    def validate(self) -> None:
        """Fail at startup, not at the first request, when the configuration is unsafe."""
        if self.auth_mode == "dev" and (self.is_production or not self.allow_dev_auth):
            raise RuntimeError(
                "AUTH_MODE=dev is refused: it needs ALLOW_DEV_AUTH=true and APP_ENV other than 'production'."
            )
        if self.auth_mode == "supabase" and len(self.supabase_jwt_secret) < MIN_JWT_SECRET_LENGTH:
            raise RuntimeError(
                f"SUPABASE_JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters (use the project's JWT secret)."
            )
