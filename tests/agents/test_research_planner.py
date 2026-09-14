"""Tests for ResearchPlanner intake interpretation."""

import json
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fin_automation.agents.research_planner import ResearchPlanner
from fin_automation.models.common import (
    AssetType,
    InvestmentObjective,
    RequestType,
    RiskTolerance,
    TimeHorizon,
)
from fin_automation.models.intake import (
    IntakeResult,
    InvestorProfile,
    ResearchRequest,
    ResearchScope,
)

from fin_automation.exceptions import ClarificationRequiredError

def create_complete_intake_result(
    workflow_id: UUID,
    original_prompt: str = (
        "Compare three international stocks for long-term growth."
    ),
) -> IntakeResult:
    """Create a valid intake result that needs no clarification."""

    return IntakeResult(
        workflow_id=workflow_id,
        research_request=ResearchRequest(
            workflow_id=workflow_id,
            original_prompt=original_prompt,
            research_question=(
                "Which international stocks are most aligned with "
                "a long-term growth objective?"
            ),
            request_type=RequestType.CANDIDATE_DISCOVERY,
        ),
        investor_profile=InvestorProfile(
            workflow_id=workflow_id,
            risk_tolerance=RiskTolerance.HIGH,
            investment_objective=InvestmentObjective.GROWTH,
            time_horizon=TimeHorizon.LONG_TERM,
            growth_or_income_preference="growth",
            geographic_preferences=["international"],
        ),
        research_scope=ResearchScope(
            workflow_id=workflow_id,
            asset_types=[AssetType.PUBLIC_STOCK],
            candidate_limit=3,
            geographic_scope=["international"],
        ),
        assumptions=[],
        missing_fields=[],
        requires_clarification=False,
        clarification_questions=[],
    )


def create_incomplete_intake_result(
    workflow_id: UUID,
    original_prompt: str = "Find an investment for me.",
) -> IntakeResult:
    """Create a valid intake result that requires clarification."""

    return IntakeResult(
        workflow_id=workflow_id,
        research_request=ResearchRequest(
            workflow_id=workflow_id,
            original_prompt=original_prompt,
            research_question=(
                "Identify an investment candidate."
            ),
            request_type=RequestType.CANDIDATE_DISCOVERY,
        ),
        investor_profile=InvestorProfile(
            workflow_id=workflow_id,
            risk_tolerance=None,
            investment_objective=None,
            time_horizon=None,
        ),
        research_scope=ResearchScope(
            workflow_id=workflow_id,
            asset_types=[AssetType.PUBLIC_STOCK],
            candidate_limit=3,
        ),
        assumptions=[],
        missing_fields=[
            "risk_tolerance",
            "investment_objective",
            "time_horizon",
        ],
        requires_clarification=True,
        clarification_questions=[
            "What level of investment risk are you comfortable with?",
            "What is your primary investment objective?",
            "What is your intended investment time horizon?",
        ],
    )


def create_uninitialized_planner(
    raw_result: object,
) -> ResearchPlanner:
    """Create a planner with a mocked smolagents run method.

    This bypasses ToolCallingAgent initialization because these tests
    exercise only the application wrapper around the framework.
    """

    planner = object.__new__(ResearchPlanner)
    planner.run = Mock(return_value=raw_result)

    return planner


def test_parse_intake_result_accepts_existing_model() -> None:
    """An existing IntakeResult should be returned unchanged."""

    expected_result = create_complete_intake_result(
        workflow_id=uuid4()
    )

    parsed_result = ResearchPlanner._parse_intake_result(
        expected_result
    )

    assert parsed_result is expected_result


def test_parse_intake_result_accepts_dictionary() -> None:
    """A dictionary should be validated as an IntakeResult."""

    expected_result = create_complete_intake_result(
        workflow_id=uuid4()
    )

    raw_result = expected_result.model_dump(
        mode="json"
    )

    parsed_result = ResearchPlanner._parse_intake_result(
        raw_result
    )

    assert parsed_result == expected_result


def test_parse_intake_result_accepts_json_string() -> None:
    """A JSON string should be validated as an IntakeResult."""

    expected_result = create_complete_intake_result(
        workflow_id=uuid4()
    )

    raw_result = expected_result.model_dump_json()

    parsed_result = ResearchPlanner._parse_intake_result(
        raw_result
    )

    assert parsed_result == expected_result


def test_parse_intake_result_accepts_json_code_fence() -> None:
    """A Markdown-fenced JSON result should be normalized."""

    expected_result = create_complete_intake_result(
        workflow_id=uuid4()
    )

    raw_result = (
        "```json\n"
        f"{expected_result.model_dump_json()}\n"
        "```"
    )

    parsed_result = ResearchPlanner._parse_intake_result(
        raw_result
    )

    assert parsed_result == expected_result


def test_parse_intake_result_rejects_empty_result() -> None:
    """An empty final answer should be rejected."""

    with pytest.raises(
        ValueError,
        match="returned an empty intake result",
    ):
        ResearchPlanner._parse_intake_result("   ")


def test_parse_intake_result_rejects_invalid_json() -> None:
    """Non-JSON agent output should be rejected."""

    with pytest.raises(
        ValueError,
        match="did not return valid JSON",
    ):
        ResearchPlanner._parse_intake_result(
            "This is not a JSON object."
        )


def test_parse_intake_result_rejects_invalid_contract() -> None:
    """JSON that violates IntakeResult should be rejected."""

    raw_result = json.dumps(
        {
            "workflow_id": str(uuid4()),
            "requires_clarification": False,
        }
    )

    with pytest.raises(
        ValueError,
        match=(
            "does not satisfy the IntakeResult contract"
        ),
    ):
        ResearchPlanner._parse_intake_result(raw_result)


def test_remove_markdown_code_fence_accepts_plain_json() -> None:
    """Plain JSON should remain unchanged."""

    raw_text = '{"status": "valid"}'

    cleaned_text = (
        ResearchPlanner._remove_markdown_code_fence(
            raw_text
        )
    )

    assert cleaned_text == raw_text


def test_remove_markdown_code_fence_removes_json_fence() -> None:
    """An outer JSON code fence should be removed."""

    raw_text = (
        "```json\n"
        '{"status": "valid"}\n'
        "```"
    )

    cleaned_text = (
        ResearchPlanner._remove_markdown_code_fence(
            raw_text
        )
    )

    assert cleaned_text == '{"status": "valid"}'


def test_validate_intake_identity_accepts_matching_result() -> None:
    """Matching prompt and workflow identity should pass."""

    workflow_id = uuid4()
    original_prompt = (
        "Compare three international stocks for long-term growth."
    )

    intake_result = create_complete_intake_result(
        workflow_id=workflow_id,
        original_prompt=original_prompt,
    )

    ResearchPlanner._validate_intake_identity(
        intake_result=intake_result,
        original_prompt=original_prompt,
        workflow_id=workflow_id,
    )


def test_validate_intake_identity_rejects_workflow_mismatch() -> None:
    """A result from another workflow should be rejected."""

    requested_workflow_id = uuid4()

    intake_result = create_complete_intake_result(
        workflow_id=uuid4()
    )

    with pytest.raises(
        ValueError,
        match=(
            "intake result workflow_id does not match"
        ),
    ):
        ResearchPlanner._validate_intake_identity(
            intake_result=intake_result,
            original_prompt=(
                intake_result
                .research_request
                .original_prompt
            ),
            workflow_id=requested_workflow_id,
        )


def test_validate_intake_identity_rejects_modified_prompt() -> None:
    """The model must preserve the original request exactly."""

    workflow_id = uuid4()

    intake_result = create_complete_intake_result(
        workflow_id=workflow_id,
        original_prompt="Modified prompt.",
    )

    with pytest.raises(
        ValueError,
        match=(
            "did not preserve the original prompt exactly"
        ),
    ):
        ResearchPlanner._validate_intake_identity(
            intake_result=intake_result,
            original_prompt="Original prompt.",
            workflow_id=workflow_id,
        )


def test_interpret_intake_returns_validated_result() -> None:
    """The planner should return a valid IntakeResult."""

    workflow_id = uuid4()
    original_prompt = (
        "Compare three international stocks for long-term growth."
    )

    expected_result = create_complete_intake_result(
        workflow_id=workflow_id,
        original_prompt=original_prompt,
    )

    planner = create_uninitialized_planner(
        raw_result=expected_result.model_dump_json()
    )

    result = planner.interpret_intake(
        original_prompt=original_prompt,
        workflow_id=workflow_id,
    )

    assert result == expected_result


def test_interpret_intake_calls_smolagents_run_once() -> None:
    """Intake interpretation should invoke the agent once."""

    workflow_id = uuid4()
    original_prompt = (
        "Compare three international stocks for long-term growth."
    )

    expected_result = create_complete_intake_result(
        workflow_id=workflow_id,
        original_prompt=original_prompt,
    )

    planner = create_uninitialized_planner(
        raw_result=expected_result.model_dump_json()
    )

    planner.interpret_intake(
        original_prompt=original_prompt,
        workflow_id=workflow_id,
    )

    planner.run.assert_called_once()

    call_args = planner.run.call_args

    assert call_args.kwargs["reset"] is True
    assert isinstance(call_args.args[0], str)


def test_interpret_intake_task_contains_original_prompt() -> None:
    """The task supplied to smolagents should contain the request."""

    workflow_id = uuid4()
    original_prompt = "Analyze Company A."

    expected_result = create_complete_intake_result(
        workflow_id=workflow_id,
        original_prompt=original_prompt,
    )

    planner = create_uninitialized_planner(
        raw_result=expected_result.model_dump_json()
    )

    planner.interpret_intake(
        original_prompt=original_prompt,
        workflow_id=workflow_id,
    )

    task = planner.run.call_args.args[0]
    task_payload = json.loads(task)

    assert task_payload["original_prompt"] == original_prompt
    assert task_payload["workflow_id"] == str(workflow_id)


def test_interpret_intake_returns_clarification_result() -> None:
    """Incomplete intake should return clarification information."""

    workflow_id = uuid4()
    original_prompt = "Find an investment for me."

    expected_result = create_incomplete_intake_result(
        workflow_id=workflow_id,
        original_prompt=original_prompt,
    )

    planner = create_uninitialized_planner(
        raw_result=expected_result.model_dump_json()
    )

    result = planner.interpret_intake(
        original_prompt=original_prompt,
        workflow_id=workflow_id,
    )

    assert result.requires_clarification is True
    assert set(result.missing_fields) == {
        "risk_tolerance",
        "investment_objective",
        "time_horizon",
    }
    assert result.clarification_questions


def test_interpret_intake_rejects_modified_prompt() -> None:
    """The planner should reject an altered original prompt."""

    workflow_id = uuid4()

    returned_result = create_complete_intake_result(
        workflow_id=workflow_id,
        original_prompt="Modified by model.",
    )

    planner = create_uninitialized_planner(
        raw_result=returned_result.model_dump_json()
    )

    with pytest.raises(
        ValueError,
        match=(
            "did not preserve the original prompt exactly"
        ),
    ):
        planner.interpret_intake(
            original_prompt="Original user prompt.",
            workflow_id=workflow_id,
        )


def test_interpret_intake_rejects_wrong_workflow() -> None:
    """The planner should reject output from another workflow."""

    requested_workflow_id = uuid4()
    original_prompt = "Analyze Company A."

    returned_result = create_complete_intake_result(
        workflow_id=uuid4(),
        original_prompt=original_prompt,
    )

    planner = create_uninitialized_planner(
        raw_result=returned_result.model_dump_json()
    )

    with pytest.raises(
        ValueError,
        match=(
            "intake result workflow_id does not match"
        ),
    ):
        planner.interpret_intake(
            original_prompt=original_prompt,
            workflow_id=requested_workflow_id,
        )


def test_interpret_intake_rejects_blank_prompt_before_run() -> None:
    """A blank prompt should fail before invoking smolagents."""

    planner = create_uninitialized_planner(
        raw_result=""
    )

    with pytest.raises(
        ValueError,
        match="original prompt cannot be empty",
    ):
        planner.interpret_intake(
            original_prompt="   ",
            workflow_id=uuid4(),
        )

    planner.run.assert_not_called()

def test_clarification_gate_allows_complete_intake() -> None:
    """Complete intake should pass the clarification gate."""

    intake_result = create_complete_intake_result(
        workflow_id=uuid4()
    )

    ResearchPlanner.ensure_ready_for_planning(
        intake_result=intake_result,
    )


def test_clarification_gate_rejects_incomplete_intake() -> None:
    """Incomplete intake should stop research planning."""

    intake_result = create_incomplete_intake_result(
        workflow_id=uuid4()
    )

    with pytest.raises(
        ClarificationRequiredError,
        match="user clarification is required",
    ):
        ResearchPlanner.ensure_ready_for_planning(
            intake_result=intake_result,
        )


def test_clarification_error_preserves_missing_fields() -> None:
    """The clarification error should preserve missing fields."""

    intake_result = create_incomplete_intake_result(
        workflow_id=uuid4()
    )

    with pytest.raises(
        ClarificationRequiredError,
    ) as error_info:
        ResearchPlanner.ensure_ready_for_planning(
            intake_result=intake_result,
        )

    error = error_info.value

    assert error.missing_fields == [
        "risk_tolerance",
        "investment_objective",
        "time_horizon",
    ]


def test_clarification_error_preserves_questions() -> None:
    """The clarification error should preserve user questions."""

    intake_result = create_incomplete_intake_result(
        workflow_id=uuid4()
    )

    with pytest.raises(
        ClarificationRequiredError,
    ) as error_info:
        ResearchPlanner.ensure_ready_for_planning(
            intake_result=intake_result,
        )

    error = error_info.value

    assert error.clarification_questions == (
        intake_result.clarification_questions
    )
    assert error.clarification_questions


def test_interpret_and_validate_returns_complete_intake() -> None:
    """Guarded interpretation should return complete intake."""

    workflow_id = uuid4()
    original_prompt = (
        "Compare three international stocks for long-term growth."
    )

    expected_result = create_complete_intake_result(
        workflow_id=workflow_id,
        original_prompt=original_prompt,
    )

    planner = create_uninitialized_planner(
        raw_result=expected_result.model_dump_json()
    )

    result = planner.interpret_and_validate_intake(
        original_prompt=original_prompt,
        workflow_id=workflow_id,
    )

    assert result == expected_result
    assert result.requires_clarification is False


def test_interpret_and_validate_stops_incomplete_intake() -> None:
    """Guarded interpretation should stop incomplete intake."""

    workflow_id = uuid4()
    original_prompt = "Find an investment for me."

    incomplete_result = create_incomplete_intake_result(
        workflow_id=workflow_id,
        original_prompt=original_prompt,
    )

    planner = create_uninitialized_planner(
        raw_result=incomplete_result.model_dump_json()
    )

    with pytest.raises(
        ClarificationRequiredError,
    ) as error_info:
        planner.interpret_and_validate_intake(
            original_prompt=original_prompt,
            workflow_id=workflow_id,
        )

    assert error_info.value.missing_fields
    assert error_info.value.clarification_questions