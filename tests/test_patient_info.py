import pytest

from src.appointment_assistance.intents import AppointmentIntent
from src.appointment_assistance.patient_info import (
    PatientInformationCollector,
)


def test_collector_starts_empty():
    collector = PatientInformationCollector()

    assert collector.info.patient_name is None
    assert collector.info.doctor_name is None
    assert collector.info.preferred_date is None
    assert collector.info.preferred_time is None
    assert collector.info.appointment_id is None


def test_collector_stores_patient_and_doctor_information():
    collector = PatientInformationCollector()

    collector.update(
        patient_name="Mehar",
        doctor_name="Dr. Ahmed",
    )

    assert collector.info.patient_name == "Mehar"
    assert collector.info.doctor_name == "Dr. Ahmed"


def test_collector_stores_optional_date_and_time_preferences():
    collector = PatientInformationCollector()

    collector.update(
        patient_name="Mehar",
        doctor_name="Dr. Ahmed",
        preferred_date="Monday",
        preferred_time="10:00 AM",
    )

    assert collector.info.preferred_date == "Monday"
    assert collector.info.preferred_time == "10:00 AM"


def test_booking_requires_patient_and_doctor():
    collector = PatientInformationCollector()

    missing = collector.missing_fields(
        AppointmentIntent.BOOK_APPOINTMENT
    )

    assert missing == ["patient_name", "doctor_name"]


def test_booking_does_not_require_preferred_date_or_time():
    collector = PatientInformationCollector()

    collector.update(
        patient_name="Mehar",
        doctor_name="Dr. Ahmed",
    )

    assert collector.is_ready(
        AppointmentIntent.BOOK_APPOINTMENT
    )


def test_availability_requires_patient_and_doctor():
    collector = PatientInformationCollector()

    collector.update(patient_name="Mehar")

    missing = collector.missing_fields(
        AppointmentIntent.DOCTOR_AVAILABILITY
    )

    assert missing == ["doctor_name"]


def test_reschedule_requires_patient_and_appointment_id():
    collector = PatientInformationCollector()

    collector.update(patient_name="Mehar")

    missing = collector.missing_fields(
        AppointmentIntent.RESCHEDULE_APPOINTMENT
    )

    assert missing == ["appointment_id"]


def test_reschedule_becomes_ready_with_appointment_id():
    collector = PatientInformationCollector()

    collector.update(
        patient_name="Mehar",
        appointment_id="APT-123",
    )

    assert collector.is_ready(
        AppointmentIntent.RESCHEDULE_APPOINTMENT
    )


def test_update_ignores_empty_values():
    collector = PatientInformationCollector()

    collector.update(
        patient_name="Mehar",
        doctor_name="Dr. Ahmed",
    )

    collector.update(
        patient_name="",
        doctor_name="",
    )

    assert collector.info.patient_name == "Mehar"
    assert collector.info.doctor_name == "Dr. Ahmed"