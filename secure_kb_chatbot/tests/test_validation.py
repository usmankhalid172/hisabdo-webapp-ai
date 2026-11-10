"""SQA: Validation - every bad input is rejected with 422 and a field location."""

import pytest

from conftest import OWNER


def field_of(response):
    assert response.status_code == 422, response.text
    return [e["loc"][-1] for e in response.json()["detail"]]


@pytest.mark.parametrize(
    "body, field",
    [
        ({}, "name"),
        ({"name": ""}, "name"),
        ({"name": "   "}, "name"),
        ({"name": "x" * 121}, "name"),
        ({"name": "A", "email": "not-an-email"}, "email"),
        ({"name": "A", "phone": "call me"}, "phone"),
        ({"name": "A", "status": "vip"}, "status"),
        ({"name": "A", "last_contact": "2026-13-45"}, "last_contact"),
        ({"name": "A", "tags": [""]}, 0),
        ({"name": "A", "id": "C-999"}, "id"),  # server-owned fields can't be set
        ({"name": "A", "business_id": "B-002"}, "business_id"),
    ],
)
def test_customer_validation(client, body, field):
    assert field in field_of(client.post("/api/customers", json=body, headers=OWNER))


@pytest.mark.parametrize(
    "body, field",
    [
        ({}, "title"),
        ({"title": "t", "status": "blocked"}, "status"),
        ({"title": "t", "priority": "urgent"}, "priority"),
        ({"title": "t", "due_date": "tomorrow"}, "due_date"),
        ({"title": "t", "assignee_id": "U-999"}, "assignee_id"),
        ({"title": "t", "customer_id": "C-999"}, "customer_id"),
    ],
)
def test_task_validation(client, body, field):
    assert field in field_of(client.post("/api/tasks", json=body, headers=OWNER))


@pytest.mark.parametrize(
    "body, field",
    [
        ({}, "content"),
        ({"content": "  "}, "content"),
        ({"content": "x" * 5001}, "content"),
        ({"content": "ok", "author_id": "U-002"}, "author_id"),  # can't impersonate an author
        ({"content": "ok", "customer_id": "C-999"}, "customer_id"),
    ],
)
def test_note_validation(client, body, field):
    assert field in field_of(client.post("/api/notes", json=body, headers=OWNER))


@pytest.mark.parametrize(
    "body",
    [
        {"amount": 1000},  # missing customer
        {"customer_id": "C-001", "amount": 0},
        {"customer_id": "C-001", "amount": -5},
        {"customer_id": "C-001", "amount": 10.005},
        {"customer_id": "C-001", "amount": 100, "amount_paid": 150},
        {"customer_id": "C-001", "amount": 100, "amount_paid": -1},
        {"customer_id": "C-001", "amount": 100, "issue_date": "2026-10-10", "due_date": "2026-10-01"},
        {"customer_id": "C-001", "amount": "a lot"},
        {"customer_id": "C-999", "amount": 100},
    ],
)
def test_receivable_validation(client, body):
    assert client.post("/api/receivables", json=body, headers=OWNER).status_code == 422


def test_payable_requires_vendor(client):
    assert "vendor_name" in field_of(client.post("/api/payables", json={"amount": 10}, headers=OWNER))


def test_patch_revalidates_the_merged_record(client):
    # amount_paid alone looks fine, but it exceeds the stored amount (40,000).
    r = client.patch("/api/receivables/R-001", json={"amount_paid": 50000}, headers=OWNER)
    assert r.status_code == 422
    # Lowering amount below what's already paid is caught the same way.
    r = client.patch("/api/receivables/R-002", json={"amount": 10000}, headers=OWNER)
    assert r.status_code == 422
    assert client.get("/api/receivables/R-002", headers=OWNER).json()["amount"] == 65000  # unchanged


def test_patch_cannot_null_a_required_field(client):
    assert "name" in field_of(client.patch("/api/customers/C-001", json={"name": None}, headers=OWNER))


@pytest.mark.parametrize("message", ["", "   ", "x" * 4001])
def test_chat_message_validation(client, message):
    assert client.post("/api/chat", json={"message": message}, headers=OWNER).status_code == 422


def test_malformed_json_body(client):
    r = client.post("/api/customers", content="{not json", headers={**OWNER, "Content-Type": "application/json"})
    assert r.status_code == 422
