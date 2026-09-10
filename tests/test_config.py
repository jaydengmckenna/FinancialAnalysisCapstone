"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from fin_automation.config import Settings


REQUIRED_ENVIRONMENT_VARIABLES = [
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "TAVILY_API_KEY",
    "MODEL_ID",
]


def test_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load valid environment variables."""

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("MODEL_ID", "test-model")

    settings = Settings(_env_file=None)

    assert settings.openai_api_key.get_secret_value() == "test-openai-key"
    assert str(settings.openai_base_url) == "https://example.com/v1"
    assert settings.tavily_api_key.get_secret_value() == "test-tavily-key"
    assert settings.model_id == "test-model"


def test_settings_reject_missing_required_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings should reject missing required configuration."""

    for variable_name in REQUIRED_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_reject_invalid_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings should reject an invalid OpenAI base URL."""

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "not-a-valid-url")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("MODEL_ID", "test-model")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_secret_values_are_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings representations should not expose API-key values."""

    monkeypatch.setenv("OPENAI_API_KEY", "sensitive-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("TAVILY_API_KEY", "sensitive-tavily-key")
    monkeypatch.setenv("MODEL_ID", "test-model")

    settings = Settings(_env_file=None)
    settings_representation = repr(settings)

    assert "sensitive-openai-key" not in settings_representation
    assert "sensitive-tavily-key" not in settings_representation