"""Research Planning Agent implementation using smolagents."""

import json
from collections.abc import Mapping
from uuid import UUID

from pydantic import BaseModel, ValidationError
from smolagents import Model, ToolCallingAgent

from fin_automation.models.intake import IntakeResult
from fin_automation.prompts.intake import (
    INTAKE_SYSTEM_PROMPT,
    build_intake_messages,
)


class ResearchPlanner(ToolCallingAgent):
    """Interpret intake and create financial research plans.

    The Research Planner uses the smolagents framework for model
    execution. Python and Pydantic remain responsible for validating
    the final structured result.
    """

    def __init__(
        self,
        model_to_use: Model,
    ) -> None:
        """Initialize the Research Planning Agent.

        Args:
            model_to_use: A smolagents-compatible model instance.
        """

        super().__init__(
            tools=[],
            model=model_to_use,
            instructions=INTAKE_SYSTEM_PROMPT,
            max_steps=2,
            name="research_planner_agent",
            description=(
                "Interprets financial research intake and creates "
                "bounded research plans."
            ),
        )

    def interpret_intake(
        self,
        original_prompt: str,
        workflow_id: UUID,
    ) -> IntakeResult:
        """Interpret a user prompt as a validated IntakeResult.

        Args:
            original_prompt: The user's original financial-research
                request.
            workflow_id: UUID identifying the current workflow.

        Returns:
            A validated IntakeResult.

        Raises:
            ValueError: If the agent response is missing, malformed,
                does not preserve the original prompt, or uses the
                wrong workflow identifier.
        """

        messages = build_intake_messages(
            original_prompt=original_prompt,
            workflow_id=workflow_id,
        )

        task = messages[1]["content"]

        raw_result = self.run(
            task,
            reset=True,
        )

        intake_result = self._parse_intake_result(
            raw_result
        )

        self._validate_intake_identity(
            intake_result=intake_result,
            original_prompt=original_prompt,
            workflow_id=workflow_id,
        )

        return intake_result

    @staticmethod
    def _parse_intake_result(
        raw_result: object,
    ) -> IntakeResult:
        """Convert the agent's final answer into IntakeResult.

        Args:
            raw_result: Final value returned by the smolagents agent.

        Returns:
            A validated IntakeResult.

        Raises:
            ValueError: If the final answer cannot be interpreted as
                an IntakeResult.
        """

        if isinstance(raw_result, IntakeResult):
            return raw_result

        if isinstance(raw_result, BaseModel):
            raw_result = raw_result.model_dump(
                mode="json"
            )

        if isinstance(raw_result, Mapping):
            try:
                return IntakeResult.model_validate(
                    dict(raw_result)
                )
            except ValidationError as error:
                raise ValueError(
                    "The agent returned an invalid intake result."
                ) from error

        raw_text = str(raw_result).strip()

        if not raw_text:
            raise ValueError(
                "The agent returned an empty intake result."
            )

        cleaned_text = (
            ResearchPlanner._remove_markdown_code_fence(
                raw_text
            )
        )

        try:
            parsed_json = json.loads(cleaned_text)
        except json.JSONDecodeError as error:
            raise ValueError(
                "The agent did not return valid JSON."
            ) from error

        try:
            return IntakeResult.model_validate(
                parsed_json
            )
        except ValidationError as error:
            raise ValueError(
                "The agent returned JSON that does not satisfy "
                "the IntakeResult contract."
            ) from error

    @staticmethod
    def _remove_markdown_code_fence(
        text: str,
    ) -> str:
        """Remove one optional Markdown JSON code fence.

        The intake prompt instructs the agent not to use code fences,
        but this normalization makes parsing resilient to that common
        formatting behavior.

        Args:
            text: Agent-produced final answer.

        Returns:
            Text with an optional outer code fence removed.
        """

        stripped_text = text.strip()

        if not stripped_text.startswith("```"):
            return stripped_text

        lines = stripped_text.splitlines()

        if len(lines) < 3:
            return stripped_text

        if lines[0].strip() not in {
            "```",
            "```json",
            "```JSON",
        }:
            return stripped_text

        if lines[-1].strip() != "```":
            return stripped_text

        return "\n".join(lines[1:-1]).strip()

    @staticmethod
    def _validate_intake_identity(
        intake_result: IntakeResult,
        original_prompt: str,
        workflow_id: UUID,
    ) -> None:
        """Validate the result against its originating request.

        Pydantic validates the internal IntakeResult structure. These
        checks verify that the model result belongs to the requested
        workflow and preserves the original prompt.

        Args:
            intake_result: Validated intake returned by the agent.
            original_prompt: Original request supplied by the caller.
            workflow_id: Workflow identifier supplied by the caller.

        Raises:
            ValueError: If the result does not correspond to the
                originating request.
        """

        if intake_result.workflow_id != workflow_id:
            raise ValueError(
                "The intake result workflow_id does not match the "
                "requested workflow."
            )

        if (
            intake_result.research_request.workflow_id
            != workflow_id
        ):
            raise ValueError(
                "The research request workflow_id does not match the "
                "requested workflow."
            )

        if (
            intake_result.investor_profile.workflow_id
            != workflow_id
        ):
            raise ValueError(
                "The investor profile workflow_id does not match the "
                "requested workflow."
            )

        if (
            intake_result.research_scope.workflow_id
            != workflow_id
        ):
            raise ValueError(
                "The research scope workflow_id does not match the "
                "requested workflow."
            )

        if (
            intake_result.research_request.original_prompt
            != original_prompt
        ):
            raise ValueError(
                "The intake result did not preserve the original "
                "prompt exactly."
            )