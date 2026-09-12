from dataclasses import dataclass

from src.appointment_assistance.api_contract import (
    AppointmentApiContract,
    get_api_contract,
)
from src.appointment_assistance.intents import (
    AppointmentIntent,
    detect_intent,
)
from src.appointment_assistance.patient_info import (
    PatientInformation,
    PatientInformationCollector,
)


@dataclass(frozen=True)
class AppointmentWorkflowResult:
    """Result returned by the appointment assistance workflow."""

    intent: AppointmentIntent
    response: str
    api_contract: AppointmentApiContract | None
    patient_info: PatientInformation
    missing_fields: list[str]


_RESPONSES = {
    AppointmentIntent.DOCTOR_AVAILABILITY: (
        "I can help you check a doctor's available appointment slots."
    ),
    AppointmentIntent.BOOK_APPOINTMENT: (
        "I can help you book an appointment."
    ),
    AppointmentIntent.RESCHEDULE_APPOINTMENT: (
        "I can help you reschedule your appointment."
    ),
    AppointmentIntent.UNKNOWN: (
        "I can help with doctor availability, booking appointments, "
        "or rescheduling appointments. Please tell me what you would like to do."
    ),
}


_MISSING_FIELD_RESPONSES = {
    "patient_name": "May I have your name?",
    "doctor_name": "Which doctor would you like to see?",
    "appointment_id": "Please provide your appointment ID.",
}


def _build_response(
    intent: AppointmentIntent,
    missing_fields: list[str],
    patient_info: PatientInformation,
) -> str:
    """Build the next conversational response."""

    if intent == AppointmentIntent.UNKNOWN:
        return _RESPONSES[intent]

    if missing_fields:
        return _MISSING_FIELD_RESPONSES[missing_fields[0]]

    if intent == AppointmentIntent.DOCTOR_AVAILABILITY:
        if patient_info.preferred_date:
            return (
                "Thank you. I have your doctor and preferred date. "
                "The next step is to check the doctor's actual available slots."
            )

        return (
            "Thank you. I have the doctor information. "
            "What date would you prefer, or would you like to see the "
            "doctor's available dates?"
        )

    if intent == AppointmentIntent.BOOK_APPOINTMENT:
        if patient_info.preferred_date or patient_info.preferred_time:
            return (
                "Thank you. I have your appointment preferences. "
                "The next step is to check the doctor's actual availability "
                "before confirming a slot."
            )

        return (
            "Thank you. I have the required information. "
            "Would you like to provide a preferred date and time, "
            "or should we check the doctor's available slots?"
        )

    if intent == AppointmentIntent.RESCHEDULE_APPOINTMENT:
        if patient_info.preferred_date or patient_info.preferred_time:
            return (
                "Thank you. I have your new appointment preference. "
                "The next step is to check availability before confirming "
                "the rescheduled slot."
            )

        return (
            "Thank you. I have your appointment ID. "
            "Please provide your preferred new date and time, "
            "or I can help you check available options."
        )

    return _RESPONSES[intent]


def process_appointment_message(
    message: str,
    collector: PatientInformationCollector | None = None,
    *,
    patient_name: str | None = None,
    doctor_name: str | None = None,
    preferred_date: str | None = None,
    preferred_time: str | None = None,
    appointment_id: str | None = None,
) -> AppointmentWorkflowResult:
    """
    Process a patient's appointment-related message.

    The workflow detects the patient's intent, extracts information from
    the patient's message, updates the collected information, identifies
    missing required information, and maps the intent to the proposed
    backend API contract.

    Preferred date/time are treated as patient preferences only. They do
    not represent confirmed appointment availability.
    """

    if collector is None:
        collector = PatientInformationCollector()

    detected_intent = detect_intent(message)

    if detected_intent != AppointmentIntent.UNKNOWN:
        collector.current_intent = detected_intent
    elif collector.current_intent is not None:
        detected_intent = collector.current_intent

    intent = detected_intent

    # Extract information directly provided in the patient's message.
    collector.extract_from_message(message)

    # Allow callers to provide structured information explicitly as well.
    collector.update(
        patient_name=patient_name,
        doctor_name=doctor_name,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        appointment_id=appointment_id,
    )

    missing_fields = collector.missing_fields(intent)
    api_contract = get_api_contract(intent.value)

    response = _build_response(
        intent,
        missing_fields,
        collector.info,
    )

    return AppointmentWorkflowResult(
        intent=intent,
        response=response,
        api_contract=api_contract,
        patient_info=collector.info,
        missing_fields=missing_fields,
    )