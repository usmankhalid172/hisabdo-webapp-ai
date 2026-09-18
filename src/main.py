"""
HisabDo AI service — FastAPI entrypoint.

Implements the endpoints planned in Day 15 §4:
  GET  /api/v1/health
  GET  /api/v1/version
  POST /api/v1/chatbot
  POST /api/v1/categorize
  POST /api/v1/categorize/batch  (planned)

Run locally:
    uvicorn src.main:app --reload --port 8000

Then:
    curl http://localhost:8000/api/v1/health
    open http://localhost:8000/docs
"""
from fastapi import APIRouter, FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from .config import get_settings
from .errors import register_exception_handlers
from .expense_categorization.router import router as categorization_router
from .financial_assistant.router import router as chatbot_router
from .middleware import CorrelationIdMiddleware, RequestLoggingMiddleware
from .schemas import HealthResponse, VersionResponse
from .xictek_website_assistant.cors import add_xictek_cors
from .xictek_website_assistant.rate_limit import limiter
from .xictek_website_assistant.router import router as xictek_router

settings = get_settings()

app = FastAPI(
    title="HisabDo AI Service",
    version=settings.service_version,
    description="Chatbot + expense categorization AI service. Day 16 POC build on the Day 15 architecture doc.",
)

# Middleware runs outermost-added-first: correlation id is assigned before
# logging so every log line has one. Auth (Day 15 §5) is enforced per-router
# via `security.require_internal_token`, not here — see src/security.py.
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

register_exception_handlers(app)

# XICTEK website assistant's per-IP rate limiting (slowapi). Wired here
# rather than inside that module's router.py because slowapi requires the
# limiter to live on app.state and its 429 handler to be registered on the
# app itself — see xictek_website_assistant/rate_limit.py for why this
# endpoint needs it from day one.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS for the website widget, scoped to /api/v1/xictek/* only -- see
# cors.py's module docstring for why this can't just be Starlette's
# CORSMiddleware applied to the whole app.
add_xictek_cors(app)

infra_router = APIRouter(prefix="/api/v1", tags=["infra"])


@infra_router.get("/health", response_model=HealthResponse, summary="Liveness / readiness probe")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@infra_router.get("/version", response_model=VersionResponse, summary="Service & model version info")
def version() -> VersionResponse:
    return VersionResponse(
        service=settings.service_name,
        version=settings.service_version,
        model_provider=settings.llm_provider,
    )


app.include_router(infra_router)
app.include_router(chatbot_router)
app.include_router(categorization_router)
app.include_router(xictek_router)
