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

from .config import get_settings
from .errors import register_exception_handlers
from .expense_categorization.router import router as categorization_router
from .financial_assistant.router import router as chatbot_router
from .middleware import CorrelationIdMiddleware, RequestLoggingMiddleware
from .schemas import HealthResponse, VersionResponse

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
