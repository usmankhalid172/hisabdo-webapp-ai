import pytest

from src.appointment_assistance.intents import (
    AppointmentIntent,
    detect_intent,
)
from src.appointment_assistance.workflow import (
    process_appointment_message,
)

@pytest.mark.parametrize(
    "message, expected_intent",
    [
        (
            "Is Dr. Ahmed available tomorrow?",
            AppointmentIntent.DOCTOR_AVAILABILITY,
        ),
        (
            "Do you have any open slots for Dr. Khan?",
            AppointmentIntent.DOCTOR_AVAILABILITY,
        ),
        (
            "I want to book an appointment with Dr. Ahmed.",
            AppointmentIntent.BOOK_APPOINTMENT,
        ),
        (
            "I need to schedule a doctor's appointment.",
            AppointmentIntent.BOOK_APPOINTMENT,
        ),
        (
            "I need to reschedule my appointment.",
            AppointmentIntent.RESCHEDULE_APPOINTMENT,
        ),
        (
            "Can I change my appointment time?",
            AppointmentIntent.RESCHEDULE_APPOINTMENT,
        ),
        (
            "What are your hospital timings?",
            AppointmentIntent.UNKNOWN,
        ),
    ],
)
def test_detect_intent(message, expected_intent):
    assert detect_intent(message) == expected_intent


def test_detect_intent_rejects_empty_message():
    with pytest.raises(ValueError):
        detect_intent("")


def test_detect_intent_rejects_non_string_message():
    with pytest.raises(ValueError):
        detect_intent(None)


def test_availability_workflow():
    result = process_appointment_message(
        "Is Dr. Ahmed available tomorrow?"
    )

    assert result.intent == AppointmentIntent.DOCTOR_AVAILABILITY
    assert "available appointment slots" in result.response
    assert result.api_contract.method == "GET"
    assert result.api_contract.path == "/appointments/availability"


def test_booking_workflow():
    result = process_appointment_message(
        "I want to book an appointment with Dr. Ahmed."
    )

    assert result.intent == AppointmentIntent.BOOK_APPOINTMENT
    assert "book an appointment" in result.response
    assert result.api_contract.method == "POST"
    assert result.api_contract.path == "/appointments"


def test_rescheduling_workflow():
    result = process_appointment_message(
        "I need to reschedule my appointment."
    )

    assert result.intent == AppointmentIntent.RESCHEDULE_APPOINTMENT
    assert "reschedule your appointment" in result.response
    assert result.api_contract.method == "PATCH"
    assert result.api_contract.path == "/appointments/{appointment_id}"


def test_unknown_workflow():
    result = process_appointment_message(
        "What are your hospital timings?"
    )

    assert result.intent == AppointmentIntent.UNKNOWN
    assert result.api_contract is None
    assert "availability" in result.response
