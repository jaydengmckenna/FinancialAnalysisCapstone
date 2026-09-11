"""Provider-independent interface for structured model generation."""

from collections.abc import Mapping, Sequence
from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel


ModelOutputT = TypeVar(
    "ModelOutputT",
    bound=BaseModel,
)


@runtime_checkable
class ModelClient(Protocol):
    """Interface required from structured-output model clients.

    A model client receives a sequence of role-based messages and a
    Pydantic output type. The client must return a validated instance
    of the requested output type.

    This protocol does not perform an API call. Concrete
    implementations, such as OpenAIModelClient, provide the actual
    provider-specific behavior.
    """

    def generate_structured(
        self,
        messages: Sequence[Mapping[str, str]],
        output_type: type[ModelOutputT],
    ) -> ModelOutputT:
        """Generate and validate a structured model response.

        Args:
            messages: Ordered system, user, and optional assistant
                messages supplied to the language model.
            output_type: Pydantic model class that defines the required
                response structure.

        Returns:
            A validated instance of the requested Pydantic model type.
        """
        ...
        