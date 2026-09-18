"""
Path-scoped CORS for the XICTEK website assistant's endpoints only.

FastAPI/Starlette's CORSMiddleware applies to the whole ASGI app -- so
wiring XICTEK_WIDGET_ALLOWED_ORIGINS through it directly would also open
every *other* endpoint in this shared repo (HisabDo's financial_assistant
chatbot, expense_categorization, etc.) to browser-based cross-origin calls
from those same origins. That's not what a website-widget CORS setting
should imply: those other endpoints aren't meant to be called from a
browser at all. This middleware only ever touches /api/v1/xictek/* paths;
every other request passes through completely untouched.

Found missing (not just unwired) while testing the widget end-to-end: the
`widget_allowed_origins` setting already existed in config.py, but nothing
in main.py ever turned it into actual CORS headers -- so a browser widget
running on a different origin/port than the API (exactly the local dev
setup in widget/demo.html) was silently blocked by the browser itself on
every request, regardless of what the setting was configured to.
"""
from fastapi import FastAPI, Request
from starlette.responses import Response

from .config import get_xictek_settings

PATH_PREFIX = "/api/v1/xictek"
ALLOWED_METHODS = "GET, POST, OPTIONS"
ALLOWED_HEADERS = "Content-Type, X-Internal-Token"


def add_xictek_cors(app: FastAPI) -> None:
    """Registers the middleware on `app`. Call once, from main.py."""

    @app.middleware("http")
    async def xictek_cors_middleware(request: Request, call_next):
        if not request.url.path.startswith(PATH_PREFIX):
            return await call_next(request)

        origin = request.headers.get("origin")
        allowed_origins = get_xictek_settings().widget_allowed_origins
        allowed = bool(origin) and origin in allowed_origins

        if request.method == "OPTIONS":
            # Preflight: answer directly, never call_next. Browsers don't
            # send auth headers on a preflight request, so if this fell
            # through to the router's require_internal_token dependency
            # it would 401 and the real request would never even be
            # attempted -- this has to be handled before routing.
            response = Response(status_code=200 if allowed else 400)
            if allowed:
                response.headers["Access-Control-Allow-Methods"] = ALLOWED_METHODS
                response.headers["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
                response.headers["Access-Control-Max-Age"] = "600"
        else:
            response = await call_next(request)

        if allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            # So any shared HTTP cache (CDN, proxy) knows the response
            # varies by Origin and doesn't serve one visitor's
            # CORS-approved response to a different, disallowed origin.
            response.headers["Vary"] = "Origin"
        return response
