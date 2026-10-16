from fastapi import APIRouter, Depends, Header

from ..schemas import ChatbotRequest, ChatbotResponse
from ..security import require_customer_access, require_internal_token
from .service import _is_own_financial_data_query, handle_chat

router = APIRouter(
    prefix="/api/v1",
    tags=["chatbot"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/chatbot", response_model=ChatbotResponse, summary="Chatbot reply for a user message")
def chatbot(
    payload: ChatbotRequest,
    authenticated_user_id: str | None = Header(
        default=None, alias="X-Authenticated-User-ID"
    ),
) -> ChatbotResponse:
    # Financial requests require a trusted upstream customer identity.
    message_lower = payload.message.lower()
    pdf_requested = any(word in message_lower for word in (
        "pdf", "as a pdf", "download report", "pdf bana",
        "pdf mein", "pdf me", "report pdf"
    ))

    if pdf_requested and _is_own_financial_data_query(payload.message):
        require_customer_access(payload.user_id, authenticated_user_id)
        response = handle_chat(payload)
        response.reply = "Your financial summary PDF is ready to download."
        response.pdf_url = (
            "/api/v1/chatbot/financial-summary.pdf?user_id=" + payload.user_id
        )
        return response

    if _is_own_financial_data_query(payload.message):
        require_customer_access(payload.user_id, authenticated_user_id)
    return handle_chat(payload)

@router.get("/chatbot/financial-summary.pdf", summary="Download financial summary PDF")
def download_financial_summary_pdf(
    user_id: str,
    authenticated_user_id: str | None = Header(
        default=None, alias="X-Authenticated-User-ID"
    ),
):
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from ..integration.backend_client import get_backend_client
    from .pdf_reports import generate_financial_summary_pdf

    require_customer_access(user_id, authenticated_user_id)
    summary = get_backend_client().get_user_financial_summary(user_id)
    pdf_bytes = generate_financial_summary_pdf(summary)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="hisabdo-financial-summary.pdf"'
        },
    )

