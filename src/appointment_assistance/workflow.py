from dataclasses import dataclass

from src.appointment_assistance.api_contract import (
    AppointmentApiContract,
    get_api_contract,
)
from src.appointment_assistance.intents import (
    AppointmentIntent,
    detect_intent,
)


@dataclass(frozen=True)
class AppointmentWorkflowResult:
    """Result returned by the appointment assistance workflow."""

    intent: AppointmentIntent
    response: str
    api_contract: AppointmentApiContract | None


_RESPONSES = {
    AppointmentIntent.DOCTOR_AVAILABILITY: (
        "I can help you check a doctor's available appointment slots. "
        "Please provide the doctor's name and your preferred date."
    ),
    AppointmentIntent.BOOK_APPOINTMENT: (
        "I can help you book an appointment. "
        "Please provide the doctor's name and your preferred date and time."
    ),
    AppointmentIntent.RESCHEDULE_APPOINTMENT: (
        "I can help you reschedule your appointment. "
        "Please provide your appointment ID and your preferred new date and time."
    ),
    AppointmentIntent.UNKNOWN: (
        "I can help with doctor availability, booking appointments, "
        "or rescheduling appointments. Please tell me what you would like to do."
    ),
}


def process_appointment_message(message: str) -> AppointmentWorkflowResult:
    """
    Process a patient's appointment-related message.

    The workflow detects the patient's intent, provides conversational
    guidance, and maps supported intents to the proposed backend API contract.
    """
    intent = detect_intent(message)

    api_contract = get_api_contract(intent.value)

    return AppointmentWorkflowResult(
        intent=intent,
        response=_RESPONSES[intent],
        api_contract=api_contract,
    )