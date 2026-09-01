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

    # LLM provider selection: "mock" | "anthropic" | "openai"
    llm_provider: str = "mock"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Categorization
    categorization_confidence_threshold: float = 0.55


@lru_cache
def get_settings() -> Settings:
    return Settings()
