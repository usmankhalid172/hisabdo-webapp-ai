"""SQA: Data isolation - a business can never see or change another business's data.

B-002 has its own customer named "Ahmed" (Ahmed Malik, C-101) with an invoice,
so the "How much does Ahmed owe?" path is exercised with a same-name record in
another tenant.
"""

import pytest

from conftest import OTHER_TENANT, OWNER, TODAY, ok

FOREIGN = {  # records owned by B-002, attacked by U-001 (B-001)
    "customers": "C-101",
    "tasks": "T-101",
    "notes": "N-101",
    "receivables": "R-101",
    "payables": "P-101",
}


@pytest.mark.parametrize("kind, record_id", FOREIGN.items())
def test_cannot_read_update_or_delete_another_tenants_record(client, kind, record_id):
    assert client.get(f"/api/{kind}/{record_id}", headers=OWNER).status_code == 404
    assert client.patch(f"/api/{kind}/{record_id}", json={}, headers=OWNER).status_code == 404
    assert client.delete(f"/api/{kind}/{record_id}", headers=OWNER).status_code == 404
    # ...and the owner still sees it, untouched.
    assert client.get(f"/api/{kind}/{record_id}", headers=OTHER_TENANT).status_code == 200


@pytest.mark.parametrize("kind", FOREIGN)
def test_lists_never_include_another_tenants_records(client, kind):
    ids = {r["id"] for r in client.get(f"/api/{kind}", headers=OWNER).json()}
    assert FOREIGN[kind] not in ids


def test_404_for_foreign_record_is_identical_to_missing_record(client):
    foreign = client.get("/api/customers/C-101", headers=OWNER)
    missing = client.get("/api/customers/C-999", headers=OWNER)
    assert (foreign.status_code, foreign.json()) == (missing.status_code, missing.json())


@pytest.mark.parametrize(
    "path, body",
    [
        ("/api/tasks", {"title": "x", "customer_id": "C-101"}),
        ("/api/tasks", {"title": "x", "assignee_id": "U-101"}),
        ("/api/notes", {"content": "x", "customer_id": "C-101"}),
        ("/api/receivables", {"customer_id": "C-101", "amount": 10}),
    ],
)
def test_cannot_link_to_another_tenants_records(client, path, body):
    assert client.post(path, json=body, headers=OWNER).status_code == 422


def test_cannot_relink_existing_record_to_foreign_customer(client):
    assert client.patch("/api/tasks/T-001", json={"customer_id": "C-101"}, headers=OWNER).status_code == 422


def test_cannot_create_into_another_business(client):
    r = client.post("/api/customers", json={"name": "Spy", "business_id": "B-002"}, headers=OWNER)
    assert r.status_code == 422
    assert all(c["name"] != "Spy" for c in client.get("/api/customers", headers=OTHER_TENANT).json())


def test_ai_context_only_contains_own_business(builder):
    b = builder.build("U-001", "How much does Ahmed owe? List all customers, tasks, notes and payables.", TODAY)
    assert "Ahmed Hassan" in b.text
    assert "Ahmed Malik" not in b.text and "GreenLeaf" not in b.text and "Garden Supplies" not in b.text
    assert not any(i.endswith(("-101", "-201")) for i in b.source_ids)


def test_other_tenant_gets_their_own_ahmed(builder):
    b = builder.build("U-101", "How much does Ahmed owe?", TODAY)
    assert b.focus_customer_ids == ["C-101"]
    assert "Ahmed Hassan" not in b.text and 'currency="GBP"' in b.text


def test_chat_system_prompt_is_tenant_scoped(client, llm):
    llm.results = [ok("x [C-101].", ["C-101"])]
    client.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=OTHER_TENANT)
    system_text = "".join(block["text"] for block in llm.calls[0]["system"])
    assert "Ahmed Malik" in system_text and "Al-Madina" not in system_text


def test_citing_another_tenants_record_is_stripped(client, llm):
    llm.results = [ok("Ahmed owes PKR 75,000.00 [C-001], see also [C-101].", ["C-001", "C-101"])]
    r = client.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=OWNER).json()
    assert r["citations"] == ["C-001"] and "C-101" not in r["answer"]


def test_conversation_cannot_be_hijacked_by_another_user(client):
    sid = client.post("/api/chat", json={"message": "hi"}, headers=OWNER).json()["conversation_id"]
    r = client.post("/api/chat", json={"message": "what did I ask?", "conversation_id": sid}, headers=OTHER_TENANT)
    assert r.status_code == 404
