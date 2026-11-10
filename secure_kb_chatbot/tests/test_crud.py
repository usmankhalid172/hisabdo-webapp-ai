"""SQA: Customers, Tasks, Notes (+ receivables/payables) - CRUD operations."""

import pytest

from conftest import OWNER


def test_customer_crud_lifecycle(client):
    r = client.post("/api/customers", json={"name": "Imran Butt", "company": "Butt Stores", "status": "active",
                                            "email": "IMRAN@Butt.example", "phone": "+92 333 0000000"}, headers=OWNER)
    assert r.status_code == 201
    created = r.json()
    assert created["id"] == "C-102"  # IDs are global, so the next free number across all businesses
    assert created["business_id"] == "B-001" and created["email"] == "imran@butt.example"

    assert client.get(f"/api/customers/{created['id']}", headers=OWNER).json() == created
    assert created["id"] in [c["id"] for c in client.get("/api/customers", headers=OWNER).json()]

    r = client.patch(f"/api/customers/{created['id']}", json={"status": "churned", "tags": ["vip"]}, headers=OWNER)
    assert r.status_code == 200
    assert r.json()["status"] == "churned" and r.json()["tags"] == ["vip"]
    assert r.json()["name"] == "Imran Butt"  # untouched fields are kept

    assert client.delete(f"/api/customers/{created['id']}", headers=OWNER).status_code == 204
    assert client.get(f"/api/customers/{created['id']}", headers=OWNER).status_code == 404


def test_task_crud_lifecycle(client):
    body = {"title": "Restock flour", "priority": "high", "due_date": "2026-10-09",
            "assignee_id": "U-003", "customer_id": "C-003"}
    t = client.post("/api/tasks", json=body, headers=OWNER).json()
    assert t["status"] == "open" and t["assignee_id"] == "U-003" and t["due_date"] == "2026-10-09"

    t = client.patch(f"/api/tasks/{t['id']}", json={"status": "done"}, headers=OWNER).json()
    assert t["status"] == "done" and t["priority"] == "high"

    t = client.patch(f"/api/tasks/{t['id']}", json={"customer_id": None}, headers=OWNER).json()
    assert t["customer_id"] is None  # explicit null clears an optional link

    assert client.delete(f"/api/tasks/{t['id']}", headers=OWNER).status_code == 204


def test_note_author_and_timestamp_are_set_by_server(client):
    n = client.post("/api/notes", json={"content": "Visited the shop", "customer_id": "C-002"}, headers=OWNER).json()
    assert n["author_id"] == "U-001" and n["created_at"]
    n2 = client.patch(f"/api/notes/{n['id']}", json={"content": "Visited the shop twice"}, headers=OWNER).json()
    assert n2["content"] == "Visited the shop twice"
    assert n2["author_id"] == "U-001" and n2["created_at"] == n["created_at"]
    assert client.delete(f"/api/notes/{n['id']}", headers=OWNER).status_code == 204


def test_receivable_balance_and_state_are_derived(client):
    r = client.post("/api/receivables", json={"customer_id": "C-005", "amount": 15000, "amount_paid": 5000,
                                              "issue_date": "2026-10-01", "due_date": "2026-10-31"}, headers=OWNER).json()
    assert r["outstanding"] == 10000 and r["state"] == "partially_paid"
    r = client.patch(f"/api/receivables/{r['id']}", json={"amount_paid": 15000}, headers=OWNER).json()
    assert r["outstanding"] == 0 and r["state"] == "paid"


def test_payable_crud_and_overdue_state(client):
    p = client.post("/api/payables", json={"vendor_name": "Lahore Flour Mills", "amount": 99999.99,
                                           "due_date": "2026-10-01"}, headers=OWNER).json()
    assert p["amount"] == 99999.99 and p["state"] == "overdue"  # money round-trips exactly
    assert client.delete(f"/api/payables/{p['id']}", headers=OWNER).status_code == 204


def test_deleting_customer_unlinks_tasks_and_notes(client):
    c = client.post("/api/customers", json={"name": "Temp"}, headers=OWNER).json()
    t = client.post("/api/tasks", json={"title": "x", "customer_id": c["id"]}, headers=OWNER).json()
    n = client.post("/api/notes", json={"content": "y", "customer_id": c["id"]}, headers=OWNER).json()
    assert client.delete(f"/api/customers/{c['id']}", headers=OWNER).status_code == 204
    assert client.get(f"/api/tasks/{t['id']}", headers=OWNER).json()["customer_id"] is None
    assert client.get(f"/api/notes/{n['id']}", headers=OWNER).json()["customer_id"] is None


@pytest.mark.parametrize("kind", ["customers", "tasks", "notes", "receivables", "payables"])
def test_list_returns_only_seeded_business_records(client, kind):
    records = client.get(f"/api/{kind}", headers=OWNER).json()
    assert records and all(r["business_id"] == "B-001" for r in records)


def test_crud_changes_reach_the_ai_context(client):
    """The chatbot reads live data: a new invoice shows up in the next context."""
    client.post("/api/receivables", json={"customer_id": "C-005", "amount": 7500, "invoice_number": "INV-2000"},
                headers=OWNER)
    ctx = client.get("/api/context", params={"q": "How much does Nadia owe?"}, headers=OWNER).json()["context"]
    assert 'invoice="INV-2000"' in ctx and 'outstanding_balance="7500.00"' in ctx
