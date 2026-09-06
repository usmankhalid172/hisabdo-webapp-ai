from typing import Dict, List

from .knowledge_base import load_doctor_knowledge_base
from .prompts import build_grounded_prompt
from .retriever import DoctorRetriever


FALLBACK_MESSAGE = (
    "I couldn't find that information in the available doctor records."
)


def _format_doctor_context(doctors: List[Dict]) -> str:
    """Convert retrieved doctor records into grounded context."""

    context_parts = []

    for doctor in doctors:
        schedule = doctor.get("schedule", {})

        schedule_text = ", ".join(
            f"{day}: {hours}"
            for day, hours in schedule.items()
        )

        context_parts.append(
            f"Doctor: {doctor.get('name', 'Unknown')}\n"
            f"Specialty: {doctor.get('specialty', 'Not available')}\n"
            f"Qualifications: "
            f"{doctor.get('qualifications', 'Not available')}\n"
            f"Schedule: "
            f"{schedule_text or 'Not available'}"
        )

    return "\n\n".join(context_parts)


class DoctorInformationService:
    """Doctor information retrieval and grounded response pipeline."""

    def __init__(
        self,
        documents: List[Dict] | None = None,
        retriever: DoctorRetriever | None = None,
    ):
        if documents is None:
            documents = load_doctor_knowledge_base()

        self.documents = documents
        self.retriever = retriever or DoctorRetriever(documents)

    def answer(self, question: str) -> Dict:
        """Retrieve doctor information and return a grounded response."""

        if not isinstance(question, str) or not question.strip():
            return {
                "answer": FALLBACK_MESSAGE,
                "source": "doctor_knowledge_base",
                "retrieved": False,
            }

        matches = self.retriever.retrieve(
            question,
            top_k=3,
        )

        if not matches:
            return {
                "answer": FALLBACK_MESSAGE,
                "source": "doctor_knowledge_base",
                "retrieved": False,
            }

        context = _format_doctor_context(matches)

        grounded_prompt = build_grounded_prompt(
            question,
            context,
        )

        # Sprint 1: return the grounded prompt for LLM integration.
        # The .NET/API integration can pass this prompt to the approved LLM.
        return {
            "answer": grounded_prompt,
            "source": "doctor_knowledge_base",
            "retrieved": True,
            "retrieved_doctors": [
                doctor["name"]
                for doctor in matches
            ],
        }