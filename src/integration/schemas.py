from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    """Application-facing request for an AI chat operation."""

    message: str = Field(
        ...,
        min_length=1,
        description="User's AI request/message.",
    )

    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation/session identifier.",
    )

    user_id: Optional[str] = Field(
        default=None,
        description="Optional application user identifier.",
    )

    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional application context.",
    )


class AIChatResponse(BaseModel):
    """Normalized application-facing AI response."""

    status: str = Field(
        ...,
        description="Processing status, e.g. success or error.",
    )

    response: str = Field(
        ...,
        description="AI-generated response text.",
    )

    request_id: Optional[str] = Field(
        default=None,
        description="Identifier used for request tracing.",
    )

    sources: Optional[List[Any]] = Field(
        default=None,
        description="Optional retrieved knowledge sources.",
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional response metadata.",
    )


class AIErrorResponse(BaseModel):
    """Standardized application-facing integration error."""

    status: str = "error"

    error_code: str = Field(
        ...,
        description="Application-level error code.",
    )

    message: str = Field(
        ...,
        description="Human-readable error message.",
    )

    request_id: Optional[str] = Field(
        default=None,
        description="Identifier used for request tracing.",
    )