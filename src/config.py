from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    ART_API_BASE_URL: str = "https://api.artic.edu/api/v1"
    ART_API_TIMEOUT_SECONDS: float = 10.0
    ART_API_CACHE_TTL_SECONDS: int = 3600

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

MIN_PLACES_PER_PROJECT = 1
MAX_PLACES_PER_PROJECT = 10
