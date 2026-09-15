from dataclasses import dataclass
import re

from src.appointment_assistance.intents import AppointmentIntent


@dataclass
class PatientInformation:
    """Information collected from a patient during appointment assistance."""

    patient_name: str | None = None
    doctor_name: str | None = None
    preferred_date: str | None = None
    preferred_time: str | None = None
    appointment_id: str | None = None


class PatientInformationCollector:
    """Collect and validate information needed for an appointment workflow."""

    def __init__(self) -> None:
        self.info = PatientInformation()
        self.current_intent: AppointmentIntent | None = None

    def update(
        self,
        patient_name: str | None = None,
        doctor_name: str | None = None,
        preferred_date: str | None = None,
        preferred_time: str | None = None,
        appointment_id: str | None = None,
    ) -> PatientInformation:
        """Update the collected patient information."""

        if patient_name:
            self.info.patient_name = patient_name.strip()

        if doctor_name:
            self.info.doctor_name = doctor_name.strip()

        if preferred_date:
            self.info.preferred_date = preferred_date.strip()

        if preferred_time:
            self.info.preferred_time = preferred_time.strip()

        if appointment_id:
            self.info.appointment_id = appointment_id.strip()

        return self.info

    def extract_from_message(self, message: str) -> PatientInformation:
        """
        Extract basic appointment information from a patient message.

        This intentionally uses simple deterministic patterns. It does not
        assume that a preferred date/time is an available appointment slot.
        """

        if not isinstance(message, str):
            raise ValueError("message must be a string")

        normalized_message = " ".join(message.strip().split())

        if not normalized_message:
            raise ValueError("message must not be empty")

        extracted = {}

        # Example: "My name is Mehar"
        patient_match = re.search(
            r"\bmy name is\s+([A-Za-z][A-Za-z'-]*)",
            normalized_message,
            re.IGNORECASE,
        )

        if patient_match:
            extracted["patient_name"] = patient_match.group(1).strip()

        # Example: "Dr. Ahmed" or "Dr Ahmed"
        doctor_match = re.search(
            r"\bDr\.?\s+([A-Za-z][A-Za-z'-]*)",
            normalized_message,
            re.IGNORECASE,
        )

        if doctor_match:
            extracted["doctor_name"] = (
                f"Dr. {doctor_match.group(1).strip()}"
            )

        # Example: "APT-123", "APT123", "appointment ID APT-123"
        appointment_match = re.search(
            r"\b(?:appointment\s*(?:id|number)?\s*[:#-]?\s*)?"
            r"(APT[-_]?\d+)\b",
            normalized_message,
            re.IGNORECASE,
        )

        if appointment_match:
            extracted["appointment_id"] = appointment_match.group(1).upper()

        # Example: "Monday", "tomorrow", "25 September"
        date_match = re.search(
            r"\b("
            r"today|tomorrow|monday|tuesday|wednesday|thursday|"
            r"friday|saturday|sunday|"
            r"\d{1,2}(?:st|nd|rd|th)?\s+"
            r"(?:january|february|march|april|may|june|july|august|"
            r"september|october|november|december)"
            r")\b",
            normalized_message,
            re.IGNORECASE,
        )

        if date_match:
            extracted["preferred_date"] = date_match.group(1)

        # Example: "10 AM", "10:30 PM"
        time_match = re.search(
            r"\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM))\b",
            normalized_message,
            re.IGNORECASE,
        )

        if time_match:
            extracted["preferred_time"] = time_match.group(1)

        return self.update(**extracted)

    def missing_fields(self, intent: AppointmentIntent) -> list[str]:
        """Return information still required for the selected appointment intent."""

        missing = []

        if intent == AppointmentIntent.DOCTOR_AVAILABILITY:
            if not self.info.doctor_name:
                missing.append("doctor_name")

        elif intent == AppointmentIntent.BOOK_APPOINTMENT:
            if not self.info.patient_name:
                missing.append("patient_name")

            if not self.info.doctor_name:
                missing.append("doctor_name")

        elif intent == AppointmentIntent.RESCHEDULE_APPOINTMENT:
            if not self.info.appointment_id:
                missing.append("appointment_id")

        return missing

    def is_ready(self, intent: AppointmentIntent) -> bool:
        """Return True when all required information has been collected."""

        return not self.missing_fields(intent)