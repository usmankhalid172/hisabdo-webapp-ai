"""
Cross-cutting request handling per Day 15 §8:
  - correlation / request-ID propagation
  - structured request logging

Implemented as ASGI middleware so every route gets this for free.
Service-to-service auth (Day 15 §5) now lives in `security.py` as a
FastAPI dependency instead of middleware — see that file for why.
"""
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .logging_config import logger, timed_ms


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Reads X-Request-ID if the backend sent one, else generates one, and
    echoes it back on the response so both sides can trace the same request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        logger.info(
            "request_handled",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": timed_ms(start),
            },
        )
        return response
