from functools import lru_cache
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "hisabdo-ai-service"
    service_version: str = "0.1.0-poc"

    internal_service_token: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    app_env: str = "development"

    llm_provider: str = "mock"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    categorization_confidence_threshold: float = 0.55

    @model_validator(mode="after")
    def validate_security_settings(self):
        if self.app_env.lower() == "production":
            if len(self.internal_service_token) < 32:
                raise ValueError(
                    "INTERNAL_SERVICE_TOKEN must be at least 32 characters in production"
                )
            if len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be at least 32 characters in production"
                )
            if self.jwt_secret_key.lower() in {
                "secret", "changeme", "change-me", "change-me-dev-token"
            }:
                raise ValueError("JWT_SECRET_KEY is not secure")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
