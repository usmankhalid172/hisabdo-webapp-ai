from pathlib import Path

from src.doctor_information.knowledge_base import (
    load_doctor_knowledge_base,
)
from src.doctor_information.retriever import DoctorRetriever
from src.doctor_information.prompts import (
    SYSTEM_PROMPT,
    build_grounded_prompt,
)

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sample_doctor_knowledge.json"
)


def create_retriever():
    documents = load_doctor_knowledge_base(DATA_PATH)
    return DoctorRetriever(documents)


def test_dermatology_query_returns_dermatologist():
    retriever = create_retriever()

    results = retriever.retrieve(
        "Who specializes in dermatology?"
    )

    assert len(results) > 0
    assert results[0]["name"] == "Dr. Ahmed Khan"
    assert results[0]["specialty"] == "Dermatology"


def test_doctor_name_query_returns_correct_doctor():
    retriever = create_retriever()

    results = retriever.retrieve(
        "What is Dr. Ahmed Khan's specialty?"
    )

    assert len(results) > 0
    assert results[0]["name"] == "Dr. Ahmed Khan"


def test_schedule_query_retrieves_doctor():
    retriever = create_retriever()

    results = retriever.retrieve(
        "When is Dr. Ahmed Khan available?"
    )

    assert len(results) > 0
    assert results[0]["name"] == "Dr. Ahmed Khan"
    assert "Monday" in results[0]["schedule"]


def test_monday_query_returns_doctor_with_monday_schedule():
    retriever = create_retriever()

    results = retriever.retrieve(
        "Which doctors are available Monday?"
    )

    assert len(results) > 0


def test_unknown_doctor_does_not_match():
    retriever = create_retriever()

    results = retriever.retrieve(
        "What is Dr. Unknown's schedule?"
    )

    assert results == []


def test_unknown_specialty_does_not_match():
    retriever = create_retriever()

    results = retriever.retrieve(
        "Which doctor specializes in neurosurgery?"
    )

    assert results == []


def test_empty_query_returns_no_results():
    retriever = create_retriever()

    results = retriever.retrieve("")

    assert results == []
def test_grounded_prompt_contains_retrieved_doctor_information():
    context = (
        "Doctor: Dr. Ahmed Khan\n"
        "Specialty: Dermatology\n"
        "Qualifications: MBBS, FCPS\n"
        "Schedule: Monday: 10:00 AM - 2:00 PM"
    )

    prompt = build_grounded_prompt(
        "What is Dr. Ahmed Khan's specialty?",
        context,
    )

    assert "Dr. Ahmed Khan" in prompt
    assert "Dermatology" in prompt
    assert "MBBS, FCPS" in prompt
    assert "Use only facts supported by the retrieved information." in prompt


def test_grounded_prompt_prevents_hallucinated_information():
    prompt = build_grounded_prompt(
        "When is Dr. Ahmed Khan available?",
        "Doctor: Dr. Ahmed Khan\nSpecialty: Dermatology",
    )

    assert "Do not invent missing doctor information." in prompt
    assert (
        "I couldn't find that information in the available doctor records."
        in prompt
    )


def test_system_prompt_prevents_doctor_information_hallucination():
    assert "Use ONLY the doctor information provided in the retrieved context." in SYSTEM_PROMPT
    assert "Never invent or assume" in SYSTEM_PROMPT
    assert "Do not provide medical diagnoses" in SYSTEM_PROMPT


def test_grounded_prompt_blocks_medical_advice():
    prompt = build_grounded_prompt(
        "What treatment should I take?",
        "Doctor: Dr. Ahmed Khan\nSpecialty: Dermatology",
    )

    assert "Do not provide diagnosis or treatment advice." in prompt