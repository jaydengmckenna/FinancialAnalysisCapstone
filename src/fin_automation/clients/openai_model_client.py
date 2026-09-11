"""OpenAI implementation of structured model generation."""

from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from fin_automation.clients.model_client import ModelClient


ModelOutputT = TypeVar(
    "ModelOutputT",
    bound=BaseModel,
)


class OpenAIModelClient:
    """Generate structured Pydantic outputs using OpenAI."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        client: Any | None = None,
    ) -> None:
        """Initialize the OpenAI model client.

        Args:
            api_key: API key used when constructing the OpenAI SDK
                client.
            model: Model or deployment name.
            base_url: Optional OpenAI-compatible API base URL.
            timeout_seconds: Maximum request duration in seconds.
            max_retries: Number of retries delegated to the SDK.
            client: Optional preconfigured or fake SDK client.

        Raises:
            ValueError: If configuration values are invalid.
        """

        if not model.strip():
            raise ValueError(
                "The model name cannot be empty."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        if max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )

        if client is None and not api_key.strip():
            raise ValueError(
                "An API key is required when no OpenAI client is "
                "provided."
            )

        self._model = model

        if client is not None:
            self._client = client
        else:
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_seconds,
                max_retries=max_retries,
            )

    @property
    def model(self) -> str:
        """Return the configured model name."""

        return self._model

    def generate_structured(
        self,
        messages: Sequence[Mapping[str, str]],
        output_type: type[ModelOutputT],
    ) -> ModelOutputT:
        """Generate and validate a structured model response.

        The provider interprets the messages and produces data matching
        the requested Pydantic output type.

        Args:
            messages: Ordered role-based messages produced by a prompt
                builder.
            output_type: Pydantic model class defining the required
                response schema.

        Returns:
            A validated instance of the requested Pydantic model.

        Raises:
            ValueError: If the messages or output type are invalid, or
                the response contains no parsed output.
            TypeError: If the parsed result has an unexpected type.
            RuntimeError: If the provider request fails.
        """

        normalized_messages = self._validate_messages(
            messages
        )

        self._validate_output_type(output_type)

        try:
            response = self._client.responses.parse(
                model=self._model,
                input=normalized_messages,
                text_format=output_type,
            )
        except Exception as error:
            raise RuntimeError(
                "Structured model generation failed."
            ) from error

        parsed_output = response.output_parsed

        if parsed_output is None:
            raise ValueError(
                "The model response did not contain parsed "
                "structured output."
            )

        if not isinstance(parsed_output, output_type):
            raise TypeError(
                "The parsed response did not match the requested "
                f"output type {output_type.__name__}."
            )

        return parsed_output

    @staticmethod
    def _validate_messages(
        messages: Sequence[Mapping[str, str]],
    ) -> list[dict[str, str]]:
        """Validate and normalize model messages.

        Args:
            messages: Role-based messages from a prompt builder.

        Returns:
            Plain message dictionaries suitable for the provider SDK.

        Raises:
            ValueError: If no messages are supplied or any message is
                malformed.
        """

        if not messages:
            raise ValueError(
                "At least one model message is required."
            )

        allowed_roles = {
            "system",
            "developer",
            "user",
            "assistant",
        }

        normalized_messages: list[dict[str, str]] = []

        for index, message in enumerate(messages):
            role = message.get("role")
            content = message.get("content")

            if role not in allowed_roles:
                raise ValueError(
                    f"Message {index} has an unsupported role."
                )

            if content is None or not content.strip():
                raise ValueError(
                    f"Message {index} must contain nonempty content."
                )

            normalized_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return normalized_messages

    @staticmethod
    def _validate_output_type(
        output_type: type[ModelOutputT],
    ) -> None:
        """Require a Pydantic model class.

        Args:
            output_type: Proposed structured-output class.

        Raises:
            ValueError: If the object is not a Pydantic model class.
        """

        if (
            not isinstance(output_type, type)
            or not issubclass(output_type, BaseModel)
        ):
            raise ValueError(
                "output_type must be a Pydantic BaseModel class."
            )


def is_model_client(client: object) -> bool:
    """Return whether an object satisfies the ModelClient interface."""

    return isinstance(client, ModelClient)