"""
Secure Financial API — learning/demo implementation.

IMPORTANT:
- This is a teaching example, not production-ready financial software.
- Data is stored in memory and resets when the server restarts.
- Replace the demo user store and in-memory records with a database.
- Set a long random JWT_SECRET in your environment before running.
"""

import os
from datetime import date, datetime, timedelta, timezone
from typing import Literal, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

app = FastAPI(title="Secure Financial API", version="1.0.0")
bearer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # Safe for local learning only. Never use this fallback in a deployed app.
    JWT_SECRET = "LOCAL-ONLY-CHANGE-ME-before-deployment"

JWT_ALGORITHM = "HS256"
TOKEN_MINUTES = 30

# Demo users. Passwords are intentionally not implemented in this sample.
# In a real app, authenticate against a database and verify a strong password hash.
USERS = {
    "alice": {"user_id": "user_alice", "account_id": "acct_alice", "role": "user"},
    "bob": {"user_id": "user_bob", "account_id": "acct_bob", "role": "user"},
    "admin": {"user_id": "user_admin", "account_id": "acct_admin", "role": "admin"},
}

# Example financial records. Each record is explicitly associated with an account.
# "demo" and "actual" data are kept separate.
RECORDS = [
    {
        "id": "r1", "account_id": "acct_alice", "mode": "actual",
        "kind": "receivable", "amount": 1200.00, "currency": "PKR",
        "record_date": date(2026, 10, 1), "customer": "Customer A",
    },
    {
        "id": "r2", "account_id": "acct_alice", "mode": "actual",
        "kind": "payable", "amount": 300.00, "currency": "PKR",
        "record_date": date(2026, 10, 5), "customer": "Supplier A",
    },
    {
        "id": "r3", "account_id": "acct_alice", "mode": "demo",
        "kind": "receivable", "amount": 9999.00, "currency": "PKR",
        "record_date": date(2026, 10, 3), "customer": "Demo Customer",
    },
    {
        "id": "r4", "account_id": "acct_bob", "mode": "actual",
        "kind": "receivable", "amount": 7000.00, "currency": "PKR",
        "record_date": date(2026, 10, 2), "customer": "Customer B",
    },
]

class TokenRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)

class FinancialRecordOut(BaseModel):
    id: str
    kind: Literal["receivable", "payable"]
    amount: float
    currency: str
    record_date: date
    customer: str
    data_mode: Literal["demo", "actual"]

class SummaryOut(BaseModel):
    account_id: str
    data_mode: Literal["demo", "actual"]
    period_start: date
    period_end_exclusive: date
    receivables_total: float
    payables_total: float
    record_count: int
    currency: str = "PKR"

def issue_token(username: str) -> str:
    """Create a short-lived signed token for a known demo user."""
    user = USERS.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["user_id"],
        "account_id": user["account_id"],
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def current_principal(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Verify bearer token and derive identity/account from the signed token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "account_id", "exp"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    account_id = payload.get("account_id")
    role = payload.get("role", "user")
    if not user_id or not account_id:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    # Re-check the account association against the server-side user registry.
    # In production, query the database for current user/account membership.
    matching_user = next(
        (u for u in USERS.values()
         if u["user_id"] == user_id and u["account_id"] == account_id),
        None,
    )
    if matching_user is None:
        raise HTTPException(status_code=403, detail="Account access not allowed")

    return {"user_id": user_id, "account_id": account_id, "role": role}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/demo-token")
def create_demo_token(request: TokenRequest):
    """
    LOCAL TESTING ONLY: issues a token for sample usernames.
    Remove/disable this route in production and use your real login provider.
    """
    token = issue_token(request.username)
    return {"access_token": token, "token_type": "bearer", "expires_in_minutes": TOKEN_MINUTES}

def validate_period(start_date: date, end_date: date):
    # API uses [start_date, end_date): start is included, end is excluded.
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    if (end_date - start_date).days > 366:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 366 days")

def visible_records(principal, mode: str, start_date: date, end_date: date):
    validate_period(start_date, end_date)
    # Critical security rule: account_id comes from verified token, not request input.
    return [
        r for r in RECORDS
        if r["account_id"] == principal["account_id"]
        and r["mode"] == mode
        and start_date <= r["record_date"] < end_date
    ]

@app.get("/financial-records", response_model=list[FinancialRecordOut])
def get_financial_records(
    data_mode: Literal["demo", "actual"] = Query(default="actual"),
    start_date: date = Query(..., description="Inclusive start date, YYYY-MM-DD"),
    end_date: date = Query(..., description="Exclusive end date, YYYY-MM-DD"),
    principal: dict = Depends(current_principal),
):
    records = visible_records(principal, data_mode, start_date, end_date)
    return [
        {
            "id": r["id"], "kind": r["kind"], "amount": r["amount"],
            "currency": r["currency"], "record_date": r["record_date"],
            "customer": r["customer"], "data_mode": r["mode"],
        }
        for r in records
    ]

@app.get("/financial-summary", response_model=SummaryOut)
def get_financial_summary(
    data_mode: Literal["demo", "actual"] = Query(default="actual"),
    start_date: date = Query(..., description="Inclusive start date, YYYY-MM-DD"),
    end_date: date = Query(..., description="Exclusive end date, YYYY-MM-DD"),
    principal: dict = Depends(current_principal),
):
    records = visible_records(principal, data_mode, start_date, end_date)
    receivables = sum(r["amount"] for r in records if r["kind"] == "receivable")
    payables = sum(r["amount"] for r in records if r["kind"] == "payable")
    return {
        "account_id": principal["account_id"],
        "data_mode": data_mode,
        "period_start": start_date,
        "period_end_exclusive": end_date,
        "receivables_total": round(receivables, 2),
        "payables_total": round(payables, 2),
        "record_count": len(records),
        "currency": "PKR",
    }

@app.get("/me")
def who_am_i(principal: dict = Depends(current_principal)):
    """Returns identity derived from the verified token; accepts no account ID input."""
    return principal
