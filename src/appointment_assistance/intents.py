from enum import Enum


class AppointmentIntent(str, Enum):
    """Supported appointment-related patient intents."""

    DOCTOR_AVAILABILITY = "doctor_availability"
    BOOK_APPOINTMENT = "book_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    UNKNOWN = "unknown"


_INTENT_KEYWORDS = {
    AppointmentIntent.DOCTOR_AVAILABILITY: (
        "available",
        "availability",
        "free",
        "open slot",
        "slots",
        "appointment time",
        "when can i see",
        "when is",
    ),
    AppointmentIntent.BOOK_APPOINTMENT: (
        "book",
        "booking",
        "schedule",
        "appointment",
        "make an appointment",
        "want to see",
        "see a doctor",
    ),
    AppointmentIntent.RESCHEDULE_APPOINTMENT: (
        "reschedule",
        "reschedule my appointment",
        "change my appointment",
        "change appointment",
        "move my appointment",
        "change the date",
        "change the time",
        "another time",
    ),
}


def detect_intent(message: str) -> AppointmentIntent:
    """
    Detect the primary appointment intent from a patient message.

    Args:
        message: Patient's natural-language appointment request.

    Returns:
        The detected AppointmentIntent.

    Raises:
        ValueError: If message is not a non-empty string.
    """
    if not isinstance(message, str):
        raise ValueError("message must be a string")

    normalized_message = " ".join(message.lower().strip().split())

    if not normalized_message:
        raise ValueError("message must not be empty")

    # Rescheduling is checked first because it can also contain
    # generic booking words such as "appointment".
    for keyword in _INTENT_KEYWORDS[AppointmentIntent.RESCHEDULE_APPOINTMENT]:
        if keyword in normalized_message:
            return AppointmentIntent.RESCHEDULE_APPOINTMENT

    for keyword in _INTENT_KEYWORDS[AppointmentIntent.DOCTOR_AVAILABILITY]:
        if keyword in normalized_message:
            return AppointmentIntent.DOCTOR_AVAILABILITY

    for keyword in _INTENT_KEYWORDS[AppointmentIntent.BOOK_APPOINTMENT]:
        if keyword in normalized_message:
            return AppointmentIntent.BOOK_APPOINTMENT

    return AppointmentIntent.UNKNOWN