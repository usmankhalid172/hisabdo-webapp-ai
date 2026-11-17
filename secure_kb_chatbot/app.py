"""HTTP API: CRUD for business data + the context-aware chat endpoint + demo UI.

Run:   uvicorn app:default_app --factory --reload     then open http://localhost:8000
Docs:  http://localhost:8000/docs (try every CRUD endpoint from the browser)

The signed-in user comes from the ``X-User-Id`` header so the demo can switch
users. In production, take it from your auth session instead - never from a
value the client can set freely. Every route resolves the user's business and
scopes all reads/writes to it.

Status codes: 200/201/204 success; 401 missing/unknown user; 404 record or
conversation not found *or not yours*; 409 delete blocked by dependent records,
or message sent to an archived conversation; 422 validation error; 503 AI or
database unavailable.
"""

import os
import sqlite3
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import ValidationError

from chatbot import schemas
from chatbot.auth import AuthError, authenticate
from chatbot.config import Settings
from chatbot.context_builder import ContextBuilder
from chatbot.embeddings import Embedder, GeminiEmbedder
from chatbot.conversations import Conversation, ConversationArchived, ConversationNotFound, ConversationStore
from chatbot.llm import LLMClient, LLMUnavailable, make_llm_client
from chatbot.models import User
from chatbot.periods import InvalidPeriod, local_today, resolve_period
from chatbot.repository import Conflict, InvalidReference, RecordNotFound, Repository
from chatbot.retrieval import KBRetriever, NoteIndex
from chatbot.service import ChatReply, ChatService
from chatbot.vector_store import VectorStore

ROOT = Path(__file__).parent

# kind -> (create model, patch model, singular label)
CRUD = {
    "customers": (schemas.CustomerIn, schemas.CustomerPatch, "customer"),
    "tasks": (schemas.TaskIn, schemas.TaskPatch, "task"),
    "notes": (schemas.NoteIn, schemas.NotePatch, "note"),
    "receivables": (schemas.ReceivableIn, schemas.ReceivablePatch, "receivable"),
    "payables": (schemas.PayableIn, schemas.PayablePatch, "payable"),
}


def create_app(
    repo: Repository,
    llm_factory: Callable[[], LLMClient] = make_llm_client,
    today: date | None = None,
    conversations: ConversationStore | None = None,
    settings: Settings | None = None,
    embedder_factory: Callable[[], Embedder] | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.validate()  # refuse to start with an unsafe configuration
    # API documentation is not public in production.
    docs = {} if not settings.is_production else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title="Business-aware chatbot", **docs)
    builder = ContextBuilder(repo)
    conversations = conversations or ConversationStore(repo)
    state: dict = {}

    def current_date() -> date:
        return today or local_today(settings.reporting_timezone)

    def knowledge() -> tuple[KBRetriever | None, NoteIndex | None]:
        """Semantic search components, or (None, None) when embeddings aren't configured."""
        if "kb" not in state:
            try:
                factory = embedder_factory or (lambda: GeminiEmbedder(settings.embedding_model, settings.embedding_dim))
                embedder, store = factory(), VectorStore(repo)
                state["kb"] = (KBRetriever(store, embedder, settings.kb_threshold, settings.kb_top_k),
                               NoteIndex(store, embedder, settings.note_threshold))
            except Exception:  # no key: the chatbot still works, and says product info is unavailable
                state["kb"] = (None, None)
        return state["kb"]

    def chat_service() -> ChatService:
        if "chat" not in state:  # lazy: CRUD works without AI credentials
            try:
                llm = llm_factory()
            except Exception as e:  # e.g. no API key configured
                raise LLMUnavailable("The AI assistant is not configured on this server.") from e
            retriever, note_index = knowledge()
            state["chat"] = ChatService(builder, llm, conversations, today=today, retriever=retriever,
                                        note_index=note_index, timezone=settings.reporting_timezone)
        return state["chat"]

    def current_user(
        authorization: str | None = Header(default=None), x_user_id: str | None = Header(default=None)
    ) -> User:
        """AUTHENTICATION (who is calling) then the demo-data gate. Every data route depends on this."""
        try:
            user = authenticate(settings, repo, authorization, x_user_id)
        except AuthError as e:
            raise HTTPException(401, str(e), headers={"WWW-Authenticate": "Bearer"}) from None
        if repo.get_business(user.business_id).is_demo and not settings.allow_demo_data:
            raise HTTPException(403, "Demo data is disabled on this server.")
        return user

    def only_params(*allowed: str):
        """Reject any query parameter that isn't expected, so nobody can pass user_id or business_id."""
        def check(request: Request) -> None:
            unexpected = sorted(set(request.query_params.keys()) - set(allowed))
            if unexpected:
                raise HTTPException(400, "This request contains a parameter that is not allowed.")
        return Depends(check)

    def data_mode(user: User) -> str:
        return "demo" if repo.get_business(user.business_id).is_demo else "actual"

    @app.middleware("http")
    async def no_store(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"  # financial data must never be cached
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    # --- error mapping -------------------------------------------------------------

    @app.exception_handler(RecordNotFound)
    def _not_found(_: Request, e: RecordNotFound) -> JSONResponse:
        return JSONResponse({"detail": "Record not found"}, status_code=404)

    @app.exception_handler(InvalidReference)
    def _bad_ref(_: Request, e: InvalidReference) -> JSONResponse:
        detail = [{"loc": ["body", e.field], "msg": str(e), "type": "invalid_reference"}]
        return JSONResponse({"detail": detail}, status_code=422)

    @app.exception_handler(Conflict)
    def _conflict(_: Request, e: Conflict) -> JSONResponse:
        return JSONResponse({"detail": str(e)}, status_code=409)

    @app.exception_handler(ConversationNotFound)
    def _conv_not_found(_: Request, e: ConversationNotFound) -> JSONResponse:
        return JSONResponse({"detail": "Conversation not found"}, status_code=404)

    @app.exception_handler(ConversationArchived)
    def _conv_archived(_: Request, e: ConversationArchived) -> JSONResponse:
        return JSONResponse({"detail": "Conversation is archived; unarchive it to send messages."}, status_code=409)

    @app.exception_handler(InvalidPeriod)
    def _bad_period(_: Request, e: InvalidPeriod) -> JSONResponse:
        return JSONResponse({"detail": str(e)}, status_code=422)

    @app.exception_handler(LLMUnavailable)
    def _llm_down(_: Request, e: LLMUnavailable) -> JSONResponse:
        return JSONResponse({"detail": str(e)}, status_code=503)

    @app.exception_handler(sqlite3.Error)
    def _db_down(_: Request, e: sqlite3.Error) -> JSONResponse:
        return JSONResponse({"detail": "The database is temporarily unavailable."}, status_code=503)

    # --- serialization ---------------------------------------------------------------

    def out(record) -> dict:
        d = asdict(record)
        if hasattr(record, "outstanding"):
            d["outstanding"] = record.outstanding
            d["state"] = record.state(current_date())
        return d

    # --- CRUD routes (generated per entity) ------------------------------------------

    def register(kind: str, In: type, Patch: type, label: str) -> None:
        server_fields = {"author_id", "created_at"} if kind == "notes" else set()

        @app.get(f"/api/{kind}", tags=[kind], name=f"list_{kind}", dependencies=[only_params()])
        def list_records(user: User = Depends(current_user)) -> list[dict]:
            return [out(r) for r in repo.list(kind, user.business_id)]

        @app.post(f"/api/{kind}", status_code=201, tags=[kind], name=f"create_{label}")
        def create_record(body: In, user: User = Depends(current_user)) -> dict:
            values = body.model_dump()
            if kind == "notes":
                values |= {"author_id": user.id, "created_at": datetime.now().replace(microsecond=0)}
            return out(repo.create(kind, user.business_id, values))

        @app.get(f"/api/{kind}/{{record_id}}", tags=[kind], name=f"get_{label}")
        def get_record(record_id: str, user: User = Depends(current_user)) -> dict:
            return out(repo.get(kind, user.business_id, record_id))

        @app.patch(f"/api/{kind}/{{record_id}}", tags=[kind], name=f"update_{label}")
        def update_record(record_id: str, body: Patch, user: User = Depends(current_user)) -> dict:
            existing = asdict(repo.get(kind, user.business_id, record_id))
            current = {k: v for k, v in existing.items() if k in In.model_fields}
            try:
                merged = In.model_validate({**current, **body.model_dump(exclude_unset=True)})
            except ValidationError as e:  # merged record breaks a rule -> same 422 shape as a bad body
                errors = e.errors(include_url=False, include_context=False)
                raise RequestValidationError([{**err, "loc": ("body", *err["loc"])} for err in errors]) from None
            values = {k: v for k, v in merged.model_dump().items() if k not in server_fields}
            return out(repo.update(kind, user.business_id, record_id, values))

        @app.delete(f"/api/{kind}/{{record_id}}", status_code=204, tags=[kind], name=f"delete_{label}")
        def delete_record(record_id: str, user: User = Depends(current_user)) -> Response:
            repo.delete(kind, user.business_id, record_id)
            return Response(status_code=204)

    for kind, (In, Patch, label) in CRUD.items():
        register(kind, In, Patch, label)

    # --- identity, chat, debug ---------------------------------------------------------

    @app.get("/api/me", tags=["chat"])
    def me(user: User = Depends(current_user)) -> dict:
        return {"user": asdict(user), "business": asdict(repo.get_business(user.business_id)),
                "data_mode": data_mode(user)}

    @app.get("/api/reports/summary", tags=["reports"], dependencies=[only_params("period", "start", "end")])
    def report_summary(
        period: str | None = Query(None, description="Calendar month, YYYY-MM"),
        start: date | None = Query(None, description="Custom range start (inclusive)"),
        end: date | None = Query(None, description="Custom range end (inclusive)"),
        user: User = Depends(current_user),
    ) -> dict:
        """Invoices and bills ISSUED in a period, for the signed-in user's business only."""
        p = resolve_period(period, start, end, current_date(), settings.reporting_timezone, settings.max_period_days)
        business = repo.get_business(user.business_id)

        def block(items) -> dict:
            dated = [i for i in items if p.contains(i.issue_date)]
            return {
                "issued_count": len(dated),
                "issued_total": round(sum(i.amount for i in dated), 2),
                "paid_to_date": round(sum(i.amount_paid for i in dated), 2),
                "outstanding_now": round(sum(i.outstanding for i in dated), 2),
                "undated_excluded": sum(1 for i in items if i.issue_date is None),
            }

        return {
            "period": {"start": p.start, "end": p.end, "timezone": p.timezone},
            "data_mode": "demo" if business.is_demo else "actual",
            "currency": business.currency,
            "receivables": block(repo.list("receivables", business.id)),
            "payables": block(repo.list("payables", business.id)),
            "as_of": current_date(),
            "note": "Payments carry no date in this data model, so paid_to_date and outstanding_now are "
                    "as of today, not as of the period end.",
        }

    # --- conversations ----------------------------------------------------------------

    def conversation_out(c: Conversation) -> dict:
        return {
            "id": c.id,
            "title": c.title,
            "title_source": c.title_source,
            "status": c.status,
            "message_count": c.message_count,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "last_message_at": c.last_message_at,
        }

    def reply_out(reply: ChatReply, user: User) -> dict:
        r = reply.result
        return {
            "conversation_id": reply.conversation.id,
            "conversation": conversation_out(reply.conversation),
            "answer": r.answer,
            "citations": r.citations,
            "grounding": r.grounding,
            "missing_information": r.missing_information,
            "warnings": r.warnings,
            "context": {"included": reply.context_sources, "totals": reply.context_totals},
            # Source attribution: the verified KB entries this answer cited.
            "sources": reply.sources,
            "knowledge_base": {
                "status": reply.kb.status if reply.kb else "unavailable",
                "version": reply.kb.kb_version if reply.kb else None,
                "best_score": reply.kb.best_score if reply.kb else None,
                "threshold": reply.kb.threshold if reply.kb else None,
            },
            "data_mode": data_mode(user),
        }

    @app.post("/api/conversations", status_code=201, tags=["conversations"])
    def create_conversation(
        body: schemas.ConversationCreate | None = None, user: User = Depends(current_user)
    ) -> dict:
        """Start an empty conversation. Without a title, it is named from the first question."""
        return conversation_out(conversations.create(user, body.title if body else None))

    @app.get("/api/conversations", tags=["conversations"])
    def list_conversations(
        status: Literal["active", "archived"] = "active",
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user: User = Depends(current_user),
    ) -> dict:
        """The signed-in user's conversations, most recent activity first."""
        items, total = conversations.list(user, status, limit, offset)
        return {"items": [conversation_out(c) for c in items], "total": total, "limit": limit, "offset": offset}

    @app.get("/api/conversations/{conversation_id}", tags=["conversations"])
    def get_conversation(conversation_id: str, user: User = Depends(current_user)) -> dict:
        conv = conversations.get(user, conversation_id)
        messages = [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at, **m.metadata}
            for m in conversations.messages(user, conversation_id)
        ]
        return {**conversation_out(conv), "messages": messages}

    @app.patch("/api/conversations/{conversation_id}", tags=["conversations"])
    def update_conversation(
        conversation_id: str, body: schemas.ConversationPatch, user: User = Depends(current_user)
    ) -> dict:
        """Rename (``title``) and/or archive/unarchive (``status``)."""
        conv = conversations.get(user, conversation_id)
        if body.title is not None:
            conv = conversations.rename(user, conversation_id, body.title)
        if body.status is not None and body.status != conv.status:
            conv = conversations.set_status(user, conversation_id, body.status)
        return conversation_out(conv)

    @app.delete("/api/conversations/{conversation_id}", status_code=204, tags=["conversations"])
    def delete_conversation(conversation_id: str, user: User = Depends(current_user)) -> Response:
        conversations.delete(user, conversation_id)
        return Response(status_code=204)

    @app.post("/api/conversations/{conversation_id}/messages", tags=["conversations"])
    def send_message(conversation_id: str, body: schemas.MessageIn, user: User = Depends(current_user)) -> dict:
        return reply_out(chat_service().ask(user, body.message, conversation_id), user)

    @app.post("/api/chat", tags=["chat"])
    def chat(req: schemas.ChatIn, user: User = Depends(current_user)) -> dict:
        """Shortcut: send a message, starting a new conversation when ``conversation_id`` is omitted."""
        return reply_out(chat_service().ask(user, req.message, req.conversation_id), user)

    @app.get("/api/context", tags=["chat"])
    def context_preview(q: str, user: User = Depends(current_user)) -> dict:
        """Debug view: exactly the business context that would go into the system prompt."""
        bundle = builder.build(user.id, q, current_date())
        return {"context": bundle.text, "source_ids": sorted(bundle.source_ids), "included": bundle.included}

    @app.get("/api/demo-users", tags=["demo"])
    def demo_users() -> list[dict]:
        """Powers the demo UI's user switcher. Exists only in dev auth mode."""
        if settings.auth_mode != "dev":
            raise HTTPException(404, "Not found")
        users = []
        for b_id in ("B-001", "B-002", "B-003"):
            try:
                b = repo.get_business(b_id)
            except RecordNotFound:
                continue
            users += [{"id": u.id, "name": u.name, "role": u.role, "business": b.name} for u in repo.list("users", b_id)]
        return users

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(ROOT / "static" / "index.html")

    return app


def default_app() -> FastAPI:
    """App factory used by uvicorn: SQLite file DB, seeded on first run."""
    repo = Repository(os.environ.get("CHATBOT_DB", ROOT / "data" / "app.db"))
    repo.load_seed(ROOT / "data" / "seed.json")
    today = date.fromisoformat(os.environ["CHATBOT_TODAY"]) if os.environ.get("CHATBOT_TODAY") else None
    return create_app(repo, today=today)  # settings come from the environment
