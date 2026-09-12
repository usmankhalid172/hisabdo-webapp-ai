from abc import ABC, abstractmethod

import httpx

from ..config import Settings, get_settings
from ..errors import ServiceError


class DoctorLLMProvider(ABC):
    """LLM boundary for grounded doctor-information responses."""

    @abstractmethod
    def generate_reply(
        self,
        question: str,
        context: str,
    ) -> tuple[str, int | None]:
        ...


class MockDoctorLLMProvider(DoctorLLMProvider):
    """Deterministic provider for local development and tests."""

    def generate_reply(
        self,
        question: str,
        context: str,
    ) -> tuple[str, int | None]:
        reply = (
            "Based on the available doctor records:\n"
            f"{context}"
        )

        return reply, len(reply.split())


class AnthropicDoctorLLMProvider(DoctorLLMProvider):
    """Anthropic provider using the doctor-information safety prompt."""

    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set",
                status_code=500,
            )

        self._api_key = settings.anthropic_api_key

    def generate_reply(
        self,
        question: str,
        context: str,
    ) -> tuple[str, int | None]:
        system = (
            "You are the Doctor Information Assistant for the healthcare "
            "platform. Answer ONLY using the provided doctor information. "
            "Never invent doctor names, specialties, qualifications, "
            "schedules, availability, or other facts. Do not provide "
            "diagnosis, treatment, medication, prescription, or medical "
            "advice. If information is missing, say that it is not "
            "available in the doctor records. Keep the answer concise."
        )

        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 300,
                "system": system,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Doctor information:\n{context}\n\n"
                            f"User question:\n{question}"
                        ),
                    }
                ],
            },
            timeout=30,
        )

        if response.status_code >= 400:
            raise ServiceError(
                "LLM_PROVIDER_ERROR",
                "Doctor information LLM request failed",
                status_code=502,
            )

        data = response.json()
        reply = data["content"][0]["text"]
        usage = data.get("usage", {})
        tokens_used = usage.get("input_tokens", 0) + usage.get(
            "output_tokens", 0
        )

        return reply, tokens_used


class OpenAIDoctorLLMProvider(DoctorLLMProvider):
    """OpenAI provider using the doctor-information safety prompt."""

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ServiceError(
                "LLM_PROVIDER_MISCONFIGURED",
                "LLM_PROVIDER=openai but OPENAI_API_KEY is not set",
                status_code=500,
            )

        self._api_key = settings.openai_api_key

    def generate_reply(
        self,
        question: str,
        context: str,
    ) -> tuple[str, int | None]:
        system = (
            "You are the Doctor Information Assistant for the healthcare "
            "platform. Answer ONLY using the provided doctor information. "
            "Never invent doctor names, specialties, qualifications, "
            "schedules, availability, or other facts. Do not provide "
            "diagnosis, treatment, medication, prescription, or medical "
            "advice. If information is missing, say that it is not "
            "available in the doctor records. Keep the answer concise."
        )

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": (
                            f"Doctor information:\n{context}\n\n"
                            f"User question:\n{question}"
                        ),
                    },
                ],
                "max_tokens": 300,
            },
            timeout=30,
        )

        if response.status_code >= 400:
            raise ServiceError(
                "LLM_PROVIDER_ERROR",
                "Doctor information LLM request failed",
                status_code=502,
            )

        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens")

        return reply, tokens_used


def get_doctor_llm_provider() -> DoctorLLMProvider:
    settings = get_settings()

    if settings.llm_provider == "anthropic":
        return AnthropicDoctorLLMProvider(settings)

    if settings.llm_provider == "openai":
        return OpenAIDoctorLLMProvider(settings)

    return MockDoctorLLMProvider()