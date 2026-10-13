import pytest

from src.appointment_assistance.intents import (
    AppointmentIntent,
    detect_intent,
)
from src.appointment_assistance.patient_info import (
    PatientInformationCollector,
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
    assert result.patient_info.doctor_name == "Dr. Ahmed"
    assert result.patient_info.preferred_date == "tomorrow"
    assert result.missing_fields == []
    assert "actual available slots" in result.response
    assert result.api_contract.method == "GET"
    assert result.api_contract.path == "/appointments/availability"


def test_booking_workflow_requests_patient_name():
    result = process_appointment_message(
        "I want to book an appointment with Dr. Ahmed."
    )

    assert result.intent == AppointmentIntent.BOOK_APPOINTMENT
    assert result.patient_info.doctor_name == "Dr. Ahmed"
    assert result.patient_info.patient_name is None
    assert result.missing_fields == ["patient_name"]
    assert result.response == "May I have your name?"
    assert result.api_contract.method == "POST"
    assert result.api_contract.path == "/appointments"


def test_complete_booking_workflow():
    result = process_appointment_message(
        "My name is Mehar and I want to book an appointment "
        "with Dr. Ahmed on Monday at 10 AM."
    )

    assert result.intent == AppointmentIntent.BOOK_APPOINTMENT
    assert result.patient_info.patient_name == "Mehar"
    assert result.patient_info.doctor_name == "Dr. Ahmed"
    assert result.patient_info.preferred_date == "Monday"
    assert result.patient_info.preferred_time == "10 AM"
    assert result.missing_fields == []
    assert "actual availability" in result.response
    assert "confirming a slot" in result.response
    assert result.api_contract.method == "POST"
    assert result.api_contract.path == "/appointments"


def test_rescheduling_workflow_requests_appointment_id():
    result = process_appointment_message(
        "I need to reschedule my appointment."
    )

    assert result.intent == AppointmentIntent.RESCHEDULE_APPOINTMENT
    assert result.missing_fields == ["appointment_id"]
    assert result.response == "Please provide your appointment ID."
    assert result.api_contract.method == "PATCH"
    assert result.api_contract.path == "/appointments/{appointment_id}"


def test_complete_rescheduling_workflow():
    result = process_appointment_message(
        "I want to reschedule appointment APT-123 "
        "to Monday at 10 AM."
    )

    assert result.intent == AppointmentIntent.RESCHEDULE_APPOINTMENT
    assert result.patient_info.appointment_id == "APT-123"
    assert result.patient_info.preferred_date == "Monday"
    assert result.patient_info.preferred_time == "10 AM"
    assert result.missing_fields == []
    assert "check availability" in result.response
    assert "confirming the rescheduled slot" in result.response
    assert result.api_contract.method == "PATCH"
    assert result.api_contract.path == "/appointments/{appointment_id}"


def test_multi_turn_booking_workflow():
    collector = PatientInformationCollector()

    first_result = process_appointment_message(
        "I want to book an appointment with Dr. Ahmed",
        collector,
    )

    assert first_result.intent == AppointmentIntent.BOOK_APPOINTMENT
    assert first_result.response == "May I have your name?"
    assert first_result.missing_fields == ["patient_name"]

    second_result = process_appointment_message(
        "My name is Mehar and I prefer Monday at 10 AM",
        collector,
    )

    assert second_result.intent == AppointmentIntent.BOOK_APPOINTMENT
    assert second_result.patient_info.patient_name == "Mehar"
    assert second_result.patient_info.doctor_name == "Dr. Ahmed"
    assert second_result.patient_info.preferred_date == "Monday"
    assert second_result.patient_info.preferred_time == "10 AM"
    assert second_result.missing_fields == []
    assert "actual availability" in second_result.response


def test_unknown_workflow():
    result = process_appointment_message(
        "What are your hospital timings?"
    )

    assert result.intent == AppointmentIntent.UNKNOWN
    assert result.api_contract is None
    assert result.missing_fields == []
    assert "availability" in result.response