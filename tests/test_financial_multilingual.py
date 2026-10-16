
import pytest

from src.financial_assistant.service import (
    handle_chat,
    _is_pdf_request,
    _is_product_specific_query,
)
from src.schemas import ChatbotRequest


@pytest.mark.parametrize(
    "message",
    [
        # English
        "Please generate a PDF report",
        "Download my report as PDF",

        # Urdu
        "پی ڈی ایف رپورٹ بنا دیں",
        "پی ڈی ایف رپورٹ بھیج دیں",

        # Roman Urdu
        "Mujhe PDF report bana kar do",
        "PDF report download kar do",
    ],
)
def test_pdf_requests_are_recognized_in_multiple_languages(message):
    assert _is_pdf_request(message) is True


@pytest.mark.parametrize(
    "message",
    [
        "Show me a PDF report",
        "پی ڈی ایف رپورٹ بنا دیں",
        "Mujhe PDF report bana kar do",
    ],
)
def test_pdf_requests_return_transparent_guidance(message):
    request = ChatbotRequest(
        user_id="test-user",
        message=message,
        conversation_id="multilingual-test",
        history=[],
    )

    response = handle_chat(request)

    assert response.intent == "pdf_report"
    assert response.source == "verified_product_guidance"
    assert "cannot currently generate or attach" in response.reply


@pytest.mark.parametrize(
    "message",
    [
        # English
        "How do I manage expenses?",
        "How do I record income?",

        # Urdu
        "خرچ کی تفصیل کیسے دیکھوں؟",
        "آمدن کی تفصیل کیسے دیکھوں؟",
        "ادھار کیسے دیکھوں؟",
        "کھاتہ کیسے استعمال کروں؟",

        # Roman Urdu
        "Khata kaise use karun?",
        "Udhar ka record kaise dekhoon?",
    ],
)
def test_product_questions_are_recognized(message):
    assert _is_product_specific_query(message) is True
