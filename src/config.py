"""
Centralized configuration, loaded from environment (.env for local dev).

Per Day 15 §9 — environment-based configuration, no secrets committed.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "hisabdo-ai-service"
    service_version: str = "0.1.0-poc"

    # Service-to-service auth placeholder (Day 15 blocker, see Day 16 continuity plan)
    internal_service_token: str = "change-me-dev-token"

    # "production" (default, fail closed) | "development" | "test". Outside development/test the
    # placeholder token above, or any token shorter than 32 characters, is refused (see security.py).
    app_env: str = "production"

    # LLM provider selection: "mock" | "anthropic" | "openai"
    llm_provider: str = "mock"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Categorization
    categorization_confidence_threshold: float = 0.55

    # Chatbot intent router + multi-turn conversation state (financial_assistant/dialogue).
    # false = every message goes through the previous single-turn flow.
    dialogue_enabled: bool = True

    # Grounded answers from the approved KB (financial_assistant/grounding, docs/grounded-answer-rules.md):
    # cited sources, conflict notices, clarifying questions and no-source fallbacks.
    # Off until the release gate has run on it; false = the previous top-1 faq_docs.json path.
    grounded_answers_enabled: bool = False
    kb_retriever_mode: str = "auto"   # auto | hybrid (needs fastembed) | lexical


@lru_cache
def get_settings() -> Settings:
    return Settings()
