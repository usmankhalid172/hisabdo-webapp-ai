"""
Per-client-IP rate limiting for the XICTEK chat endpoint, via slowapi.

Built in now rather than deferred (per the team lead's "perfect for
production deployment" instruction) even though this is only reachable
via Swagger today — an unauthenticated-by-design public-website endpoint
is the textbook case for needing abuse protection from day one, since
"deferred" here would mean shipping the real widget integration with no
rate limiting at all.

Wiring required in main.py (see that file's comments):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

and the decorated endpoint in router.py takes `request: Request` as its
first parameter — slowapi reads the client IP off it.
"""
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded  # noqa: F401 — re-exported for main.py
from slowapi.util import get_remote_address

from .config import get_xictek_settings

limiter = Limiter(key_func=get_remote_address)


def rate_limit_string() -> str:
    return get_xictek_settings().rate_limit
