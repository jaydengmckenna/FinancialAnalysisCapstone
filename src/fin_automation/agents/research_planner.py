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
from fin_automation.exceptions import ClarificationRequiredError
from fin_automation.models.research import ResearchPlan
from fin_automation.prompts.research_planning import (
    build_research_planning_messages,
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
    @staticmethod
    def ensure_ready_for_planning(
        intake_result: IntakeResult,
    ) -> None:
        """Stop research planning when intake requires clarification.

        This is a deterministic workflow gate. The language model
        identifies missing fields and proposes clarification questions.
        Python decides whether the workflow may continue.

        Args:
        intake_result: Validated structured intake.

        Raises:
        ClarificationRequiredError: If required information is
        missing or clarification is otherwise required.
        """

        if not intake_result.requires_clarification:
            return

        raise ClarificationRequiredError(
            missing_fields=intake_result.missing_fields,
            clarification_questions=(
                intake_result.clarification_questions
            ),
        )
    def interpret_and_validate_intake(self, original_prompt: str, workflow_id: UUID,) -> IntakeResult:
        """Interpret intake and enforce the clarification gate.

        Args:
            original_prompt: The user's financial research request.
            workflow_id: Identifier for current workflow.
            
        Returns:
            a complete IntakeResult that may proceed to research planning.
        
        Raises:
            ClarificationRequiredError: if required intake information is missing.
        """
        intake_res = self.interpret_intake(
            original_prompt=original_prompt,
            workflow_id=workflow_id,
        )
        self.ensure_ready_for_planning(
            intake_result=intake_res,
        )
        return intake_res


    def create_research_plan(
        self,
        intake_result: IntakeResult,
    ) -> ResearchPlan:
        """Create a validated plan from complete intake information.

        Args:
            intake_result: Validated intake that contains all required
                investor-profile information.

        Returns:
            A validated ResearchPlan.

        Raises:
            ClarificationRequiredError: If intake still requires user
                clarification.
            ValueError: If the agent returns invalid plan data or the
                plan does not correspond to the supplied intake.
        """

        self.ensure_ready_for_planning(
            intake_result=intake_result,
        )

        messages = build_research_planning_messages(
            intake_result=intake_result,
        )

        task = messages[1]["content"]

        raw_result = self.run(
            task,
            reset=True,
        )

        research_plan = self._parse_research_plan(
            raw_result
        )

        self._validate_research_plan_identity(
            research_plan=research_plan,
            intake_result=intake_result,
        )

        return research_plan

    @staticmethod
    def _parse_research_plan(
        raw_result: object,
    ) -> ResearchPlan:
        """Convert the agent's final answer into ResearchPlan.

        Args:
            raw_result: Final value returned by the smolagents agent.

        Returns:
            A validated ResearchPlan.

        Raises:
            ValueError: If the result is empty, malformed, or violates
                the ResearchPlan contract.
        """

        if isinstance(raw_result, ResearchPlan):
            return raw_result

        if isinstance(raw_result, BaseModel):
            raw_result = raw_result.model_dump(
                mode="json"
            )

        if isinstance(raw_result, Mapping):
            try:
                return ResearchPlan.model_validate(
                    dict(raw_result)
                )
            except ValidationError as error:
                raise ValueError(
                    "The agent returned an invalid research plan."
                ) from error

        raw_text = str(raw_result).strip()

        if not raw_text:
            raise ValueError(
                "The agent returned an empty research plan."
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
                "The agent did not return valid research-plan JSON."
            ) from error

        try:
            return ResearchPlan.model_validate(
                parsed_json
            )
        except ValidationError as error:
            raise ValueError(
                "The agent returned JSON that does not satisfy "
                "the ResearchPlan contract."
            ) from error

    @staticmethod
    def _validate_research_plan_identity(
        research_plan: ResearchPlan,
        intake_result: IntakeResult,
    ) -> None:
        """Validate the plan against the intake that produced it.

        Pydantic validates the internal ResearchPlan structure. These
        checks verify that the plan remains aligned with its originating
        workflow and research scope.

        Args:
            research_plan: Plan returned by the Research Planning Agent.
            intake_result: Intake used to request the plan.

        Raises:
            ValueError: If the plan changes workflow identity, exceeds
                scope, loses named candidates, or uses inconsistent
                candidate-discovery behavior.
        """

        if (
            research_plan.workflow_id
            != intake_result.workflow_id
        ):
            raise ValueError(
                "The research plan workflow_id does not match the "
                "intake workflow."
            )

        intake_scope = intake_result.research_scope

        if (
            research_plan.candidate_limit
            != intake_scope.candidate_limit
        ):
            raise ValueError(
                "The research plan candidate_limit does not match "
                "the validated research scope."
            )

        normalized_intake_candidates = {
            candidate.casefold()
            for candidate in intake_scope.named_candidates
        }

        normalized_plan_candidates = {
            candidate.casefold()
            for candidate in research_plan.candidate_names
        }

        missing_named_candidates = (
            normalized_intake_candidates
            - normalized_plan_candidates
        )

        if missing_named_candidates:
            raise ValueError(
                "The research plan did not preserve all explicitly "
                "named candidates."
            )

        excluded_candidates = {
            candidate.casefold()
            for candidate in intake_scope.excluded_candidates
        }

        prohibited_candidates = (
            normalized_plan_candidates
            & excluded_candidates
        )

        if prohibited_candidates:
            raise ValueError(
                "The research plan includes a candidate excluded by "
                "the validated research scope."
            )

        expected_discovery = not bool(
            intake_scope.named_candidates
        )

        if (
            research_plan.candidate_discovery_required
            != expected_discovery
        ):
            raise ValueError(
                "The research plan candidate-discovery setting does "
                "not match the validated research scope."
            )

        if (
            research_plan.source_limit_per_candidate
            > 5
        ):
            raise ValueError(
                "The research plan exceeds the approved source limit "
                "per candidate."
            )

    def interpret_and_plan(self, original_prompt: str, workflow_id: UUID,) -> IntakeResult | ResearchPlan:
        """Interpret intake and create a plan when intake is complete.

        Args:
        original_prompt: Original financial-research request.
        workflow_id: Identifier for the current workflow.
    
        Returns:
        An IntakeResult when clarification is required, otherwise
        a completed ResearchPlan.
        """

        intake_result = self.interpret_intake(original_prompt=original_prompt, workflow_id=workflow_id)

        if intake_result.requires_clarification:
            return intake_result

        return self.create_research_plan(
            intake_result=intake_result
        )