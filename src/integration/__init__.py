"""FastAPI service layer for HisabDo AI modules.

Contains the application-facing API logic: request/response schemas,
endpoints for the AI Financial Assistant, and health/usage metadata.
"""
from . import schemas, app  # noqa: F401

__all__ = ["schemas", "app"]