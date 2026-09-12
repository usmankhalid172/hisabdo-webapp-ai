from typing import Dict, List

from .knowledge_base import load_doctor_knowledge_base
from .llm import DoctorLLMProvider, get_doctor_llm_provider
from .retriever import DoctorRetriever


FALLBACK_MESSAGE = (
    "I couldn't find that information in the available doctor records."
)

MEDICAL_ADVICE_MESSAGE = (
    "I can provide doctor profile, specialty, qualification, and schedule "
    "information, but I can't provide diagnosis or treatment advice."
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


def _is_medical_advice_request(question: str) -> bool:
    """Detect explicit requests for diagnosis or treatment advice."""

    text = question.lower()

    blocked_phrases = (
        "diagnose me",
        "diagnosis",
        "what disease do i have",
        "what disease do i have?",
        "what treatment should i",
        "how should i treat",
        "how do i treat",
        "treatment for",
        "what medicine should i",
        "what medication should i",
        "which medicine should i",
        "which medication should i",
        "what should i take",
        "what dose should i",
        "dosage",
        "prescription",
        "cure my",
    )

    return any(phrase in text for phrase in blocked_phrases)


class DoctorInformationService:
    """Doctor information retrieval and grounded response pipeline."""

    def __init__(
        self,
        documents: List[Dict] | None = None,
        retriever: DoctorRetriever | None = None,
        llm_provider: DoctorLLMProvider | None = None,
    ):
        if documents is None:
            documents = load_doctor_knowledge_base()

        self.documents = documents
        self.retriever = retriever or DoctorRetriever(documents)
        self.llm_provider = llm_provider or get_doctor_llm_provider()

    def answer(self, question: str) -> Dict:
        """Retrieve doctor information and return a grounded LLM response."""

        if not isinstance(question, str) or not question.strip():
            return {
                "answer": FALLBACK_MESSAGE,
                "source": "doctor_knowledge_base",
                "retrieved": False,
                "retrieved_doctors": [],
                "tokens_used": None,
            }

        if _is_medical_advice_request(question):
            return {
                "answer": MEDICAL_ADVICE_MESSAGE,
                "source": "doctor_information_safety_boundary",
                "retrieved": False,
                "retrieved_doctors": [],
                "tokens_used": None,
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
                "retrieved_doctors": [],
                "tokens_used": None,
            }

        context = _format_doctor_context(matches)

        answer, tokens_used = self.llm_provider.generate_reply(
            question,
            context,
        )

        return {
            "answer": answer,
            "source": "doctor_knowledge_base",
            "retrieved": True,
            "retrieved_doctors": [
                doctor["name"]
                for doctor in matches
            ],
            "tokens_used": tokens_used,
        }