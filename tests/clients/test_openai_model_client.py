"""Tests for the OpenAI structured-output model client."""

from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from fin_automation.clients.model_client import ModelClient
from fin_automation.clients.openai_model_client import (
    OpenAIModelClient,
    is_model_client,
)


class ExampleOutput(BaseModel):
    """Simple structured output used by model-client tests."""

    name: str
    count: int


class OtherOutput(BaseModel):
    """Different output type used to test type mismatches."""

    value: str


class FakeResponses:
    """Fake implementation of the SDK responses resource."""

    def __init__(
        self,
        parsed_output: BaseModel | None = None,
        error: Exception | None = None,
    ) -> None:
        """Initialize the fake responses resource."""

        self.parsed_output = parsed_output
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def parse(
        self,
        *,
        model: str,
        input: list[dict[str, str]],
        text_format: type[BaseModel],
    ) -> SimpleNamespace:
        """Record a request and return the configured response."""

        self.calls.append(
            {
                "model": model,
                "input": input,
                "text_format": text_format,
            }
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            output_parsed=self.parsed_output
        )


class FakeOpenAIClient:
    """Fake OpenAI SDK client used to avoid network requests."""

    def __init__(
        self,
        parsed_output: BaseModel | None = None,
        error: Exception | None = None,
    ) -> None:
        """Initialize the fake SDK client."""

        self.responses = FakeResponses(
            parsed_output=parsed_output,
            error=error,
        )


def create_messages() -> list[dict[str, str]]:
    """Create valid messages for model-client tests."""

    return [
        {
            "role": "system",
            "content": "Return structured test data.",
        },
        {
            "role": "user",
            "content": "Create an example output.",
        },
    ]


def test_openai_client_satisfies_model_client_protocol() -> None:
    """OpenAIModelClient should satisfy ModelClient structurally."""

    client = OpenAIModelClient(
        api_key="",
        model="test-model",
        client=FakeOpenAIClient(),
    )

    assert isinstance(client, ModelClient)
    assert is_model_client(client) is True


def test_model_property_returns_configured_model() -> None:
    """The client should expose its configured model name."""

    client = OpenAIModelClient(
        api_key="",
        model="test-model",
        client=FakeOpenAIClient(),
    )

    assert client.model == "test-model"


def test_generate_structured_returns_requested_model() -> None:
    """The client should return the provider's parsed model."""

    expected_output = ExampleOutput(
        name="Company A",
        count=3,
    )

    fake_sdk_client = FakeOpenAIClient(
        parsed_output=expected_output,
    )

    client = OpenAIModelClient(
        api_key="",
        model="test-model",
        client=fake_sdk_client,
    )

    result = client.generate_structured(
        messages=create_messages(),
        output_type=ExampleOutput,
    )

    assert result == expected_output
    assert isinstance(result, ExampleOutput)


def test_generate_structured_passes_model_to_provider() -> None:
    """The configured model should be passed to the SDK."""

    fake_sdk_client = FakeOpenAIClient(
        parsed_output=ExampleOutput(
            name="Company A",
            count=3,
        )
    )

    client = OpenAIModelClient(
        api_key="",
        model="configured-model",
        client=fake_sdk_client,
    )

    client.generate_structured(
        messages=create_messages(),
        output_type=ExampleOutput,
    )

    call = fake_sdk_client.responses.calls[0]

    assert call["model"] == "configured-model"


def test_generate_structured_passes_messages_to_provider() -> None:
    """Validated messages should be passed to the SDK."""

    messages = create_messages()

    fake_sdk_client = FakeOpenAIClient(
        parsed_output=ExampleOutput(
            name="Company A",
            count=3,
        )
    )

    client = OpenAIModelClient(
        api_key="",
        model="test-model",
        client=fake_sdk_client,
    )

    client.generate_structured(
        messages=messages,
        output_type=ExampleOutput,
    )

    call = fake_sdk_client.responses.calls[0]

    assert call["input"] == messages


def test_generate_structured_passes_output_type() -> None:
    """The requested Pydantic type should become text_format."""

    fake_sdk_client = FakeOpenAIClient(
        parsed_output=ExampleOutput(
            name="Company A",
            count=3,
        )
    )

    client = OpenAIModelClient(
        api_key="",
        model="test-model",
        client=fake_sdk_client,
    )

    client.generate_structured(
        messages=create_messages(),
        output_type=ExampleOutput,
    )

    call = fake_sdk_client.responses.calls[0]

    assert call["text_format"] is ExampleOutput


def test_client_rejects_empty_model_name() -> None:
    """A provider client requires a configured model."""

    with pytest.raises(
        ValueError,
        match="model name cannot be empty",
    ):
        OpenAIModelClient(
            api_key="fake-key",
            model="   ",
        )


def test_client_rejects_empty_key_without_injected_client() -> None:
    """A real SDK client requires an API key."""

    with pytest.raises(
        ValueError,
        match="API key is required",
    ):
        OpenAIModelClient(
            api_key="",
            model="test-model",
        )


def test_injected_client_does_not_require_api_key() -> None:
    """A fake injected client should not require a real API key."""

    client = OpenAIModelClient(
        api_key="",
        model="test-model",
        client=FakeOpenAIClient(),
    )

    assert client.model == "test-model"


def test_client_rejects_nonpositive_timeout() -> None:
    """The request timeout must be greater than zero."""

    with pytest.raises(
        ValueError,
        match="timeout_seconds must be greater than zero",
    ):
        OpenAIModelClient(
            api_key="fake-key",
            model="test-model",
            timeout_seconds=0,
        )


def test_client_rejects_negative_retry_count() -> None:
    """The SDK retry count cannot be negative."""

    with pytest.raises(
        ValueError,
        match="max_retries cannot be negative",
    ):
        OpenAIModelClient(
            api_key="fake-key",
            model="test-model",
            max_retries=-1,
        )


def test_generate_structured_rejects_empty_messages() -> None:
    """At least one model message should be required."""

    client = OpenAIModelClient(
        api_key="",
        model="test-model",
        client=FakeOpenAIClient(),
    )

    with pytest.raises(
        ValueError,
        match="At least one model message is required",
    ):
        client.generate_structured(
            messages=[],
            output_type=ExampleOutput,
        )


