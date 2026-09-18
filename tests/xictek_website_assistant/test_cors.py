"""Tests for cors.py's path-scoped CORS middleware.

Found missing while testing the widget end-to-end on Hamza's machine:
XICTEK_WIDGET_ALLOWED_ORIGINS existed in config.py but nothing ever
turned it into real CORS headers, so a browser widget on a different
origin than the API (exactly widget/demo.html's local setup) was
silently blocked by the browser itself on every request.
"""
import pytest

ALLOWED_ORIGIN = "http://localhost:5500"


@pytest.fixture()
def with_allowed_origin(monkeypatch):
    monkeypatch.setenv("XICTEK_WIDGET_ALLOWED_ORIGINS", f'["{ALLOWED_ORIGIN}"]')
    from src.xictek_website_assistant.config import get_xictek_settings

    get_xictek_settings.cache_clear()
    yield
    get_xictek_settings.cache_clear()


def test_preflight_from_allowed_origin_succeeds(client, with_allowed_origin):
    resp = client.options(
        "/api/v1/xictek/chat",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-internal-token",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "POST" in resp.headers["access-control-allow-methods"]
    assert "x-internal-token" in resp.headers["access-control-allow-headers"].lower()


def test_preflight_does_not_require_auth_token(client, with_allowed_origin):
    # Browsers never send custom headers (like our auth token) on a
    # preflight OPTIONS request -- if this reached the router's
    # require_internal_token dependency it would 401 and the real
    # request would never be attempted. No X-Internal-Token header here
    # on purpose.
    resp = client.options(
        "/api/v1/xictek/chat",
        headers={"Origin": ALLOWED_ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200


def test_preflight_from_disallowed_origin_fails(client, with_allowed_origin):
    resp = client.options(
        "/api/v1/xictek/chat",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 400
    assert "access-control-allow-origin" not in resp.headers


def test_preflight_with_no_origins_configured_fails(client):
    # Default state (nothing set): the endpoint should still work fine
    # for direct/same-origin callers (Swagger, curl, server-to-server),
    # it just shouldn't grant any browser cross-origin access.
    resp = client.options(
        "/api/v1/xictek/chat",
        headers={"Origin": ALLOWED_ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 400


def test_actual_request_from_allowed_origin_gets_cors_header(client, auth_headers, with_allowed_origin):
    resp = client.post(
        "/api/v1/xictek/chat",
        headers={**auth_headers, "Origin": ALLOWED_ORIGIN},
        json={"message": "hi", "conversation_id": "cors-test"},
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_actual_request_from_disallowed_origin_has_no_cors_header(client, auth_headers, with_allowed_origin):
    # The request itself still succeeds server-side (simple requests
    # aren't blocked before reaching the server) -- but without the
    # header, the browser itself refuses to let JS read the response.
    resp = client.post(
        "/api/v1/xictek/chat",
        headers={**auth_headers, "Origin": "https://evil.example.com"},
        json={"message": "hi", "conversation_id": "cors-test"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_request_with_no_origin_header_has_no_cors_header(client, auth_headers, with_allowed_origin):
    # Server-to-server / curl / Swagger calls don't send an Origin header
    # at all -- should work exactly as before, CORS is irrelevant to them.
    resp = client.post(
        "/api/v1/xictek/chat",
        headers=auth_headers,
        json={"message": "hi", "conversation_id": "cors-test"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_other_endpoints_are_not_affected_by_xictek_cors_config(client, with_allowed_origin):
    # Path-scoping check: a completely unrelated endpoint should never
    # get CORS headers just because XICTEK_WIDGET_ALLOWED_ORIGINS is
    # configured -- that setting must not widen access to the rest of
    # this shared repo's API.
    resp = client.get("/api/v1/health", headers={"Origin": ALLOWED_ORIGIN})
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers
