"""Conversation management: create/start, IDs, rename/archive/delete, lifecycle."""

import re
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import create_app
from chatbot import LLMResult
from chatbot.conversations import DEFAULT_TITLE, ConversationStore, auto_title
from conftest import OTHER_TENANT, OWNER, TODAY, FakeLLM, ok

U002 = {"X-User-Id": "U-002"}  # same business as OWNER, different person


def new(client, headers=OWNER, **body):
    r = client.post("/api/conversations", json=body or None, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def send(client, conv_id, message="How much does Ahmed owe?", headers=OWNER):
    return client.post(f"/api/conversations/{conv_id}/messages", json={"message": message}, headers=headers)


# --- create / start -----------------------------------------------------------------------


def test_create_empty_conversation(client):
    c = new(client)
    assert c["title"] == DEFAULT_TITLE and c["title_source"] == "auto"
    assert c["status"] == "active" and c["message_count"] == 0 and c["last_message_at"] is None


def test_create_with_title(client):
    c = new(client, title="  Ahmed's dues  ")
    assert c["title"] == "Ahmed's dues" and c["title_source"] == "user"


def test_chat_without_id_starts_a_conversation(client):
    r = client.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=OWNER).json()
    assert r["conversation"]["message_count"] == 2
    assert r["conversation"]["title"] == "How much does Ahmed owe?"  # auto-titled from first question


def test_first_question_names_the_conversation_once(client):
    c = new(client)
    send(client, c["id"], "Who owes us money?")
    send(client, c["id"], "And what about suppliers?")
    assert client.get(f"/api/conversations/{c['id']}", headers=OWNER).json()["title"] == "Who owes us money?"


def test_user_title_is_never_overwritten_by_auto_title(client):
    c = new(client, title="Collections")
    send(client, c["id"])
    assert client.get(f"/api/conversations/{c['id']}", headers=OWNER).json()["title"] == "Collections"


@pytest.mark.parametrize(
    "text, title",
    [
        ("  how   much\tdoes Ahmed owe?  ", "how much does Ahmed owe?"),
        ("first line\nsecond line", "first line"),
        ("   ", DEFAULT_TITLE),
        ("word " * 30, None),  # long: cut at a word boundary
    ],
)
def test_auto_title(text, title):
    result = auto_title(text)
    if title is None:
        assert len(result) <= 60 and result.endswith("…") and not result.endswith(" …")
    else:
        assert result == title


# --- conversation IDs -----------------------------------------------------------------------


def test_ids_are_random_and_unguessable(client):
    ids = [new(client)["id"] for _ in range(5)]
    assert len(set(ids)) == 5
    assert all(re.fullmatch(r"conv_[0-9a-f]{32}", i) for i in ids)


def test_unknown_id_is_404(client):
    for r in (
        client.get("/api/conversations/conv_nope", headers=OWNER),
        client.patch("/api/conversations/conv_nope", json={"title": "x"}, headers=OWNER),
        client.delete("/api/conversations/conv_nope", headers=OWNER),
        send(client, "conv_nope"),
    ):
        assert r.status_code == 404 and r.json() == {"detail": "Conversation not found"}


# --- messages and history -------------------------------------------------------------------


def test_messages_are_stored_in_order_with_metadata(client, llm):
    llm.results = [ok("Ahmed owes PKR 85,000.00 [C-001].", ["C-001"]), ok("One open task [T-001].", ["T-001"])]
    c = new(client)
    send(client, c["id"], "How much does Ahmed owe?")
    send(client, c["id"], "Any tasks for him?")
    body = client.get(f"/api/conversations/{c['id']}", headers=OWNER).json()
    assert [(m["role"], m["content"]) for m in body["messages"]] == [
        ("user", "How much does Ahmed owe?"),
        ("assistant", "Ahmed owes PKR 85,000.00 [C-001]."),
        ("user", "Any tasks for him?"),
        ("assistant", "One open task [T-001]."),
    ]
    assert body["messages"][1]["citations"] == ["C-001"] and body["messages"][1]["grounding"] == "grounded"
    assert body["message_count"] == 4


def test_history_is_replayed_and_survives_restart(repo, client, llm):
    llm.results = [ok("PKR 85,000.00 [C-001].", ["C-001"])]
    c = new(client)
    send(client, c["id"], "How much does Ahmed owe?")

    # A brand-new app instance over the same database = a server restart.
    llm2 = FakeLLM(ok("One task [T-001].", ["T-001"]))
    restarted = TestClient(create_app(repo, llm_factory=lambda: llm2, today=TODAY))
    assert send(restarted, c["id"], "Any tasks for him?").status_code == 200
    sent = llm2.calls[0]
    assert sent["messages"] == [
        {"role": "user", "content": "How much does Ahmed owe?"},
        {"role": "assistant", "content": "PKR 85,000.00 [C-001]."},
        {"role": "user", "content": "Any tasks for him?"},
    ]
    assert "T-001" in sent["system"][1]["text"]  # "him" resolved from the persisted customer focus


def test_failed_turn_is_not_stored(client, llm):
    llm.results = [LLMResult(stop_reason="refusal", data=None)]
    c = new(client)
    r = send(client, c["id"]).json()
    assert r["grounding"] == "refused" and r["conversation_id"] == c["id"]
    assert client.get(f"/api/conversations/{c['id']}", headers=OWNER).json()["messages"] == []


def test_history_replay_is_capped(repo):
    from chatbot.service import MAX_TURNS

    user = repo.get_user("U-001")
    store = ConversationStore(repo)
    c = store.create(user)
    for i in range(MAX_TURNS + 3):
        store.append_turn(user, c.id, f"q{i}", f"a{i}", {}, [])
    turns = store.recent_turns(user, c.id, MAX_TURNS)
    assert len(turns) == MAX_TURNS and turns[0] == ("q3", "a3") and turns[-1][0] == f"q{MAX_TURNS + 2}"


# --- list ------------------------------------------------------------------------------------


def test_list_is_most_recent_first_with_pagination(client):
    a, b, c = new(client), new(client), new(client)
    send(client, a["id"])  # a now has the latest activity
    page = client.get("/api/conversations", params={"limit": 2}, headers=OWNER).json()
    assert page["total"] == 3 and len(page["items"]) == 2
    assert page["items"][0]["id"] == a["id"]
    rest = client.get("/api/conversations", params={"limit": 2, "offset": 2}, headers=OWNER).json()
    assert len(rest["items"]) == 1
    all_ids = {i["id"] for i in page["items"] + rest["items"]}
    assert all_ids == {a["id"], b["id"], c["id"]}


def test_list_empty_state(client):
    assert client.get("/api/conversations", headers=OWNER).json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


@pytest.mark.parametrize("params", [{"status": "deleted"}, {"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_list_validation(client, params):
    assert client.get("/api/conversations", params=params, headers=OWNER).status_code == 422


# --- rename ------------------------------------------------------------------------------------


def test_rename(client):
    c = new(client)
    r = client.patch(f"/api/conversations/{c['id']}", json={"title": "Supplier payments"}, headers=OWNER).json()
    assert r["title"] == "Supplier payments" and r["title_source"] == "user"


@pytest.mark.parametrize("body", [{"title": ""}, {"title": "   "}, {"title": "x" * 121}, {"title": None},
                                  {"status": "deleted"}, {"status": None}, {"id": "conv_x"}])
def test_patch_validation(client, body):
    c = new(client)
    assert client.patch(f"/api/conversations/{c['id']}", json=body, headers=OWNER).status_code == 422


# --- archive / lifecycle -------------------------------------------------------------------------


def test_archive_unarchive_lifecycle(client):
    c = new(client)
    send(client, c["id"])

    archived = client.patch(f"/api/conversations/{c['id']}", json={"status": "archived"}, headers=OWNER).json()
    assert archived["status"] == "archived"
    assert client.get("/api/conversations", headers=OWNER).json()["total"] == 0
    assert client.get("/api/conversations", params={"status": "archived"}, headers=OWNER).json()["total"] == 1

    # Archived = read-only: readable and renamable, but no new messages.
    assert client.get(f"/api/conversations/{c['id']}", headers=OWNER).json()["message_count"] == 2
    assert client.patch(f"/api/conversations/{c['id']}", json={"title": "Old"}, headers=OWNER).status_code == 200
    r = send(client, c["id"])
    assert r.status_code == 409 and "archived" in r.json()["detail"]

    client.patch(f"/api/conversations/{c['id']}", json={"status": "active"}, headers=OWNER)
    assert send(client, c["id"]).status_code == 200


def test_archived_conversation_does_not_call_the_model(client, llm):
    c = new(client)
    client.patch(f"/api/conversations/{c['id']}", json={"status": "archived"}, headers=OWNER)
    send(client, c["id"])
    assert llm.calls == []


def test_archived_mid_answer_is_not_written(repo):
    """Race: the conversation is archived while the model is still answering."""
    store = ConversationStore(repo)
    user = repo.get_user("U-001")

    class ArchivingLLM(FakeLLM):
        def generate(self, system, messages):
            store.set_status(user, conv_id, "archived")
            return ok("late answer [U-001].", ["U-001"])

    client = TestClient(create_app(repo, llm_factory=ArchivingLLM, today=TODAY, conversations=store))
    conv_id = new(client)["id"]
    assert send(client, conv_id).status_code == 409
    assert store.messages(user, conv_id) == []


# --- delete ----------------------------------------------------------------------------------------


def test_delete_hides_conversation_everywhere(client):
    c = new(client)
    send(client, c["id"])
    assert client.delete(f"/api/conversations/{c['id']}", headers=OWNER).status_code == 204
    assert client.get(f"/api/conversations/{c['id']}", headers=OWNER).status_code == 404
    assert send(client, c["id"]).status_code == 404
    assert client.patch(f"/api/conversations/{c['id']}", json={"status": "active"}, headers=OWNER).status_code == 404
    assert client.delete(f"/api/conversations/{c['id']}", headers=OWNER).status_code == 404  # not twice
    for status in ("active", "archived"):
        assert client.get("/api/conversations", params={"status": status}, headers=OWNER).json()["total"] == 0


def test_archived_conversation_can_be_deleted(client):
    c = new(client)
    client.patch(f"/api/conversations/{c['id']}", json={"status": "archived"}, headers=OWNER)
    assert client.delete(f"/api/conversations/{c['id']}", headers=OWNER).status_code == 204


def test_purge_removes_only_expired_soft_deletes(repo):
    now = [datetime(2026, 10, 1, tzinfo=timezone.utc)]
    store = ConversationStore(repo, clock=lambda: now[0])
    user = repo.get_user("U-001")
    old, recent, kept = store.create(user), store.create(user), store.create(user)
    store.append_turn(user, old.id, "q", "a", {}, [])
    store.delete(user, old.id)
    now[0] += timedelta(days=25)
    store.delete(user, recent.id)
    now[0] += timedelta(days=10)  # old: deleted 35 days ago, recent: 10 days ago

    assert store.purge_deleted(older_than=timedelta(days=30)) == 1
    with repo.connect() as conn:
        ids = {r[0] for r in conn.execute("SELECT id FROM conversations")}
        orphan_messages = conn.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (old.id,)).fetchone()
    assert ids == {recent.id, kept.id} and orphan_messages[0] == 0


# --- privacy / isolation -----------------------------------------------------------------------------


@pytest.mark.parametrize("intruder", [U002, OTHER_TENANT], ids=["same-business colleague", "other business"])
def test_conversations_are_private_to_their_creator(client, intruder):
    c = new(client)
    send(client, c["id"])
    assert client.get(f"/api/conversations/{c['id']}", headers=intruder).status_code == 404
    assert client.patch(f"/api/conversations/{c['id']}", json={"title": "x"}, headers=intruder).status_code == 404
    assert client.delete(f"/api/conversations/{c['id']}", headers=intruder).status_code == 404
    assert send(client, c["id"], headers=intruder).status_code == 404
    assert client.get("/api/conversations", headers=intruder).json()["total"] == 0
    assert client.get(f"/api/conversations/{c['id']}", headers=OWNER).status_code == 200  # untouched


def test_conversation_endpoints_require_a_user(client):
    assert client.get("/api/conversations").status_code == 401
    assert client.post("/api/conversations").status_code == 401
