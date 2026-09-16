"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Validated application configuration."""

    openai_api_key: SecretStr = Field(alias="OPENAI_API_KEY")
    openai_base_url: AnyHttpUrl = Field(alias="OPENAI_BASE_URL")
    tavily_api_key: SecretStr = Field(alias="TAVILY_API_KEY")
    model_id: str = Field(alias="MODEL_ID")
    output_directory: Path = Field(
        default=PROJECT_ROOT / "outputs",
        alias="OUTPUT_DIRECTORY",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache the application settings."""

    return Settings()