"""Tests for research-planning prompt construction."""

import json
from uuid import UUID, uuid4

import pytest

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
from fin_automation.prompts.research_planning import (
    RESEARCH_PLANNING_SYSTEM_PROMPT,
    build_research_planning_messages,
)


def create_complete_intake(
    workflow_id: UUID,
) -> IntakeResult:
    """Create complete intake for prompt tests."""

    original_prompt = (
        "Compare Company A and Company B for long-term growth."
    )

    return IntakeResult(
        workflow_id=workflow_id,
        research_request=ResearchRequest(
            workflow_id=workflow_id,
            original_prompt=original_prompt,
            research_question=(
                "Which candidate is most aligned with long-term "
                "growth?"
            ),
            request_type=RequestType.CANDIDATE_COMPARISON,
        ),
        investor_profile=InvestorProfile(
            workflow_id=workflow_id,
            risk_tolerance=RiskTolerance.HIGH,
            investment_objective=InvestmentObjective.GROWTH,
            time_horizon=TimeHorizon.LONG_TERM,
        ),
        research_scope=ResearchScope(
            workflow_id=workflow_id,
            asset_types=[AssetType.PUBLIC_STOCK],
            named_candidates=[
                "Company A",
                "Company B",
            ],
            candidate_limit=2,
            excluded_candidates=["Company C"],
        ),
        assumptions=[],
        missing_fields=[],
        requires_clarification=False,
        clarification_questions=[],
    )


def create_incomplete_intake(
    workflow_id: UUID,
) -> IntakeResult:
    """Create intake requiring clarification."""

    return IntakeResult(
        workflow_id=workflow_id,
        research_request=ResearchRequest(
            workflow_id=workflow_id,
            original_prompt="Find an investment.",
            research_question="Find an investment.",
            request_type=RequestType.CANDIDATE_DISCOVERY,
        ),
        investor_profile=InvestorProfile(
            workflow_id=workflow_id,
        ),
        research_scope=ResearchScope(
            workflow_id=workflow_id,
        ),
        missing_fields=[
            "risk_tolerance",
            "investment_objective",
            "time_horizon",
        ],
        requires_clarification=True,
        clarification_questions=[
            "What is your risk tolerance?",
            "What is your investment objective?",
            "What is your investment time horizon?",
        ],
    )


def test_builder_returns_system_and_user_messages() -> None:
    """Complete intake should create two planning messages."""

    messages = build_research_planning_messages(
        create_complete_intake(uuid4())
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_system_message_uses_planning_prompt() -> None:
    """The system message should use the planning instructions."""

    messages = build_research_planning_messages(
        create_complete_intake(uuid4())
    )

    assert (
        messages[0]["content"]
        == RESEARCH_PLANNING_SYSTEM_PROMPT
    )


def test_user_message_contains_valid_json() -> None:
    """The planning payload should be valid JSON."""

    messages = build_research_planning_messages(
        create_complete_intake(uuid4())
    )

    payload = json.loads(messages[1]["content"])

    assert isinstance(payload, dict)
    assert "validated_intake" in payload
    assert "output_schema" in payload


def test_workflow_id_is_preserved() -> None:
    """The planning payload should preserve workflow identity."""

    workflow_id = uuid4()

    messages = build_research_planning_messages(
        create_complete_intake(workflow_id)
    )

    payload = json.loads(messages[1]["content"])

    assert payload["workflow_id"] == str(workflow_id)


def test_named_candidates_are_preserved() -> None:
    """Planning constraints should contain named candidates."""

    messages = build_research_planning_messages(
        create_complete_intake(uuid4())
    )

    payload = json.loads(messages[1]["content"])

    assert payload["planning_constraints"][
        "named_candidates"
    ] == [
        "Company A",
        "Company B",
    ]


def test_candidate_limit_is_preserved() -> None:
    """Planning constraints should preserve the candidate limit."""

    messages = build_research_planning_messages(
        create_complete_intake(uuid4())
    )

    payload = json.loads(messages[1]["content"])

    assert payload["planning_constraints"][
        "candidate_limit"
    ] == 2


def test_excluded_candidates_are_preserved() -> None:
    """Planning constraints should preserve exclusions."""

    messages = build_research_planning_messages(
        create_complete_intake(uuid4())
    )

    payload = json.loads(messages[1]["content"])

    assert payload["planning_constraints"][
        "excluded_candidates"
    ] == ["Company C"]


def test_research_plan_schema_is_included() -> None:
    """The payload should provide the expected output schema."""

    messages = build_research_planning_messages(
        create_complete_intake(uuid4())
    )

    payload = json.loads(messages[1]["content"])
    schema = payload["output_schema"]

    assert schema["title"] == "ResearchPlan"
    assert "research_objective" in schema["properties"]
    assert "evidence_requirements" in schema["properties"]
    assert "search_queries" in schema["properties"]


def test_incomplete_intake_is_rejected() -> None:
    """Research planning should reject incomplete intake."""

    with pytest.raises(
        ValueError,
        match="requires clarification",
    ):
        build_research_planning_messages(
            create_incomplete_intake(uuid4())
        )


def test_builder_is_deterministic() -> None:
    """Identical intake should produce identical messages."""

    intake_result = create_complete_intake(uuid4())

    first_messages = build_research_planning_messages(
        intake_result
    )
    second_messages = build_research_planning_messages(
        intake_result
    )

    assert first_messages == second_messages


def test_system_prompt_preserves_scope_boundary() -> None:
    """The system prompt should prohibit research execution."""

    normalized_prompt = " ".join(
        RESEARCH_PLANNING_SYSTEM_PROMPT
        .casefold()
        .split()
    )

    assert "research planning only" in normalized_prompt
    assert "do not execute searches" in normalized_prompt
    assert "do not invent" in normalized_prompt
    assert "researchplan schema" in normalized_prompt