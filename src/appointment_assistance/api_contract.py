from dataclasses import dataclass
from enum import Enum


class AppointmentEndpoint(str, Enum):
    """Proposed backend endpoints for appointment assistance."""

    AVAILABILITY = "/appointments/availability"
    BOOK = "/appointments"
    RESCHEDULE = "/appointments/{appointment_id}"


@dataclass(frozen=True)
class AppointmentApiContract:
    """Describes how an appointment intent maps to a backend endpoint."""

    intent: str
    method: str
    path: str
    description: str


API_CONTRACTS = {
    "doctor_availability": AppointmentApiContract(
        intent="doctor_availability",
        method="GET",
        path=AppointmentEndpoint.AVAILABILITY.value,
        description="Check available appointment slots for a doctor and date.",
    ),
    "book_appointment": AppointmentApiContract(
        intent="book_appointment",
        method="POST",
        path=AppointmentEndpoint.BOOK.value,
        description="Create a new doctor appointment.",
    ),
    "reschedule_appointment": AppointmentApiContract(
        intent="reschedule_appointment",
        method="PATCH",
        path=AppointmentEndpoint.RESCHEDULE.value,
        description="Change the date or time of an existing appointment.",
    ),
}


def get_api_contract(intent: str) -> AppointmentApiContract | None:
    """Return the API contract associated with an appointment intent."""
    return API_CONTRACTS.get(intent)