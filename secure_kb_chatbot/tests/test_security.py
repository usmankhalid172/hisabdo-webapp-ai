"""Authentication, authorization, cross-customer access and demo-vs-actual data."""

import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app import create_app
from chatbot.config import Settings
from conftest import TODAY, FakeLLM, ok

SECRET = "test-only-secret-not-a-real-key-0123456789abcdef"  # generated for tests
A = "11111111-1111-4111-8111-111111111111"  # U-001, business B-001
B = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"  # U-101, business B-002
NOBODY = "99999999-9999-4999-8999-999999999999"  # valid login, not linked to any user

PROD = Settings(auth_mode="supabase", supabase_jwt_secret=SECRET, app_env="production", allow_demo_data=True)
PROD_NO_DEMO = Settings(auth_mode="supabase", supabase_jwt_secret=SECRET, app_env="production", allow_demo_data=False)
DATA_PATHS = ["/api/customers", "/api/receivables", "/api/payables", "/api/tasks", "/api/notes", "/api/me",
              "/api/conversations", "/api/reports/summary", "/api/context?q=hi"]


def token(sub=A, secret=SECRET, alg="HS256", **claims):
    body = {"sub": sub, "aud": "authenticated", "role": "authenticated", "exp": int(time.time()) + 600, **claims}
    return jwt.encode({k: v for k, v in body.items() if v is not None}, secret, algorithm=alg)


def bearer(t):
    return {"Authorization": f"Bearer {t}"}


def app_client(repo, settings, llm=None):
    return TestClient(create_app(repo, llm_factory=lambda: llm or FakeLLM(), today=TODAY, settings=settings))


# --- configuration is safe by default -------------------------------------------------------------


def test_unconfigured_server_rejects_everything(repo):
    c = app_client(repo, Settings())
    assert {c.get(p, headers={"X-User-Id": "U-001"}).status_code for p in DATA_PATHS} == {401}


@pytest.mark.parametrize(
    "settings",
    [
        Settings(auth_mode="dev", allow_dev_auth=True, app_env="production"),  # dev auth on a production server
        Settings(auth_mode="dev", allow_dev_auth=False, app_env="development"),  # dev auth without the explicit flag
        Settings(auth_mode="supabase", supabase_jwt_secret="abc", app_env="production"),  # guessable secret
        Settings(auth_mode="supabase", supabase_jwt_secret="", app_env="production"),
    ],
)
def test_unsafe_configuration_refuses_to_start(repo, settings):
    with pytest.raises(RuntimeError):
        create_app(repo, settings=settings)


def test_docs_are_hidden_in_production_only(repo, client):
    prod = app_client(repo, PROD)
    assert {prod.get(p).status_code for p in ("/docs", "/redoc", "/openapi.json")} == {404}
    assert client.get("/docs").status_code == 200  # the dev/test client


def test_demo_user_list_exists_only_in_dev_mode(repo, client):
    assert app_client(repo, PROD).get("/api/demo-users").status_code == 404
    assert client.get("/api/demo-users").status_code == 200


# --- authentication ----------------------------------------------------------------------------------


def test_no_token_is_401_everywhere(repo):
    c = app_client(repo, PROD)
    for p in DATA_PATHS:
        r = c.get(p)
        assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer", p


def test_user_id_header_is_ignored_in_production(repo):
    assert app_client(repo, PROD).get("/api/customers", headers={"X-User-Id": "U-001"}).status_code == 401


def test_valid_token_reads_own_business(repo):
    c = app_client(repo, PROD)
    me = c.get("/api/me", headers=bearer(token())).json()
    assert me["user"]["id"] == "U-001" and me["business"]["id"] == "B-001"
    customers = c.get("/api/customers", headers=bearer(token())).json()
    assert customers and all(x["business_id"] == "B-001" for x in customers)


FORGED = {
    "wrong secret": lambda: token(secret="attacker-secret-attacker-secret-0123456789"),
    "alg none": lambda: jwt.encode({"sub": A, "aud": "authenticated", "role": "authenticated",
                                    "exp": int(time.time()) + 600}, None, algorithm="none"),
    "algorithm switched to HS512": lambda: token(alg="HS512"),
    "expired": lambda: token(exp=int(time.time()) - 5),
    "no expiry": lambda: token(exp=None),
    "wrong audience": lambda: token(aud="anon"),
    "anon role": lambda: token(role="anon"),
    "service role": lambda: token(role="service_role"),
    "anonymous session": lambda: token(is_anonymous=True),
    "subject not a UUID": lambda: token(sub="U-001"),
    "subject is SQL": lambda: token(sub="' OR '1'='1"),
    "login not linked to a user": lambda: token(sub=NOBODY),
    "garbage": lambda: "not.a.jwt",
}


@pytest.mark.parametrize("name", FORGED)
def test_forged_or_invalid_tokens_are_rejected(repo, name):
    r = app_client(repo, PROD).get("/api/customers", headers=bearer(FORGED[name]()))
    assert r.status_code == 401, name


def test_auth_errors_do_not_leak_details(repo):
    r = app_client(repo, PROD).get("/api/customers", headers=bearer(token(secret="attacker-secret-attacker-secret-0123456789")))
    assert r.json() == {"detail": "Invalid authentication token."} and SECRET not in r.text


# --- cross-customer access ----------------------------------------------------------------------------

FOREIGN = {"customers": "C-101", "tasks": "T-101", "notes": "N-101", "receivables": "R-101", "payables": "P-101"}


@pytest.mark.parametrize("kind, record_id", FOREIGN.items())
def test_token_for_one_business_cannot_touch_another(repo, kind, record_id):
    c = app_client(repo, PROD)
    a, b = bearer(token(sub=A)), bearer(token(sub=B))
    foreign, missing = c.get(f"/api/{kind}/{record_id}", headers=a), c.get(f"/api/{kind}/X-404", headers=a)
    assert (foreign.status_code, foreign.json()) == (404, missing.json())  # indistinguishable from "doesn't exist"
    assert c.patch(f"/api/{kind}/{record_id}", json={}, headers=a).status_code == 404
    assert c.delete(f"/api/{kind}/{record_id}", headers=a).status_code == 404
    assert c.get(f"/api/{kind}/{record_id}", headers=b).status_code == 200  # the owner still has it


def test_identity_headers_cannot_override_the_token(repo):
    r = app_client(repo, PROD).get("/api/me", headers={**bearer(token(sub=B)), "X-User-Id": "U-001"})
    assert r.json()["business"]["id"] == "B-002"


@pytest.mark.parametrize("param", ["user_id", "business_id", "owner_id", "account_id", "as_user", "USER_ID"])
def test_parameters_that_try_to_choose_another_tenant_are_rejected(repo, param):
    c = app_client(repo, PROD)
    for path in ("/api/receivables", "/api/customers", "/api/reports/summary"):
        r = c.get(f"{path}?{param}=B-002", headers=bearer(token()))
        assert r.status_code == 400 and "B-002" not in r.text and param not in r.text  # nothing echoed back


def test_chat_context_is_built_for_the_token_holder_only(repo):
    llm = FakeLLM(ok("x [U-101].", ["U-101"]))
    app_client(repo, PROD, llm).post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=bearer(token(sub=B)))
    context = llm.calls[0]["system"][1]["text"]
    assert "Ahmed Malik" in context and "Ahmed Hassan" not in context and "Al-Madina" not in context


def test_conversation_of_one_login_is_invisible_to_another(repo):
    c = app_client(repo, PROD)
    conv = c.post("/api/conversations", headers=bearer(token(sub=A))).json()["id"]
    assert c.get(f"/api/conversations/{conv}", headers=bearer(token(sub=B))).status_code == 404


def test_responses_are_never_cacheable(repo):
    c = app_client(repo, PROD)
    for r in (c.get("/api/receivables", headers=bearer(token())), c.get("/api/receivables"),
              c.get("/api/receivables/R-101", headers=bearer(token()))):
        assert r.headers["cache-control"] == "no-store"


# --- demo vs actual data -------------------------------------------------------------------------------


def test_demo_business_is_blocked_unless_demo_data_is_enabled(repo):
    r = app_client(repo, PROD_NO_DEMO).get("/api/receivables", headers=bearer(token()))
    assert r.status_code == 403 and r.json() == {"detail": "Demo data is disabled on this server."}


def test_seed_data_is_labelled_demo_everywhere(repo):
    llm = FakeLLM(ok("Sample data: Ahmed owes PKR 85,000.00 [C-001].", ["C-001"]))
    c = app_client(repo, PROD, llm)
    h = bearer(token())
    assert c.get("/api/me", headers=h).json()["data_mode"] == "demo"
    assert c.get("/api/reports/summary?period=2026-09", headers=h).json()["data_mode"] == "demo"
    chat = c.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=h).json()
    assert chat["data_mode"] == "demo"
    assert 'data_mode="demo"' in llm.calls[0]["system"][1]["text"]  # the model is told it is sample data


def test_actual_business_is_labelled_actual_and_not_blocked(repo):
    with repo.connect() as conn:  # mark one business as real customer data
        conn.execute("UPDATE businesses SET is_demo = 0 WHERE id = 'B-002'")
    c = app_client(repo, PROD_NO_DEMO)
    assert c.get("/api/me", headers=bearer(token(sub=B))).json()["data_mode"] == "actual"
    assert c.get("/api/receivables", headers=bearer(token(sub=B))).status_code == 200
    assert c.get("/api/receivables", headers=bearer(token(sub=A))).status_code == 403  # B-001 is still demo


def test_demo_and_actual_totals_never_mix(repo):
    with repo.connect() as conn:
        conn.execute("UPDATE businesses SET is_demo = 0 WHERE id = 'B-002'")
    c = app_client(repo, PROD)
    actual = c.get("/api/reports/summary?period=2026-09", headers=bearer(token(sub=B))).json()
    assert actual["data_mode"] == "actual" and actual["receivables"]["issued_total"] == 900.0  # only its own invoice


# --- account association --------------------------------------------------------------------------------


def test_each_login_maps_to_exactly_one_user(repo):
    with pytest.raises(Exception):  # unique index: the same login can't be attached to two users
        with repo.connect() as conn:
            conn.execute("UPDATE users SET auth_id = ? WHERE id = 'U-002'", (A,))


def test_existing_database_is_migrated(tmp_path):
    """A database created before these columns existed gains them without losing data."""
    import sqlite3

    from chatbot import Repository

    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE businesses (id TEXT PRIMARY KEY, name TEXT NOT NULL, industry TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '', services TEXT NOT NULL DEFAULT '[]', hours TEXT NOT NULL DEFAULT '',
            policies TEXT NOT NULL DEFAULT '{}', currency TEXT NOT NULL DEFAULT 'PKR');
        CREATE TABLE users (id TEXT PRIMARY KEY, business_id TEXT NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL,
            role TEXT NOT NULL, timezone TEXT NOT NULL DEFAULT 'UTC');
        INSERT INTO businesses (id, name) VALUES ('B-9', 'Old Shop');
        INSERT INTO users VALUES ('U-9', 'B-9', 'Old User', 'o@example.com', 'Owner', 'UTC');
    """)
    conn.commit()
    conn.close()
    repo = Repository(path)
    assert repo.get_business("B-9").is_demo is False and repo.get_user("U-9").auth_id is None
