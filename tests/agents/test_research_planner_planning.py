"""Tests for ResearchPlanner research-plan generation."""

from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from fin_automation.agents.research_planner import ResearchPlanner
from fin_automation.exceptions import ClarificationRequiredError
from fin_automation.models.common import (
    AssetType,
    InvestmentObjective,
    RequestType,
    RiskTolerance,
    SearchPurpose,
    SourceCategory,
    TimeHorizon,
)
from fin_automation.models.intake import (
    IntakeResult,
    InvestorProfile,
    ResearchRequest,
    ResearchScope,
)
from fin_automation.models.research import (
    EvidenceRequirement,
    ResearchPlan,
    SearchQuery,
)


def create_complete_intake(
    workflow_id: UUID,
) -> IntakeResult:
    """Create valid intake for plan-generation tests."""

    return IntakeResult(
        workflow_id=workflow_id,
        research_request=ResearchRequest(
            workflow_id=workflow_id,
            original_prompt=(
                "Compare Company A and Company B for long-term "
                "growth."
            ),
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


def create_research_plan(
    workflow_id: UUID,
) -> ResearchPlan:
    """Create a valid research plan."""

    requirement = EvidenceRequirement(
        name="Revenue growth",
        description=(
            "Collect recent reported revenue-growth evidence."
        ),
        candidate_name="Company A",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[
            SourceCategory.PRIMARY,
            SourceCategory.SECONDARY,
        ],
        required=True,
    )

    query = SearchQuery(
        query="Company A annual revenue growth investor relations",
        purpose=SearchPurpose.FINANCIAL_GROWTH,
        candidate_name="Company A",
        evidence_requirement_ids=[
            requirement.requirement_id
        ],
    )

    return ResearchPlan(
        workflow_id=workflow_id,
        research_objective=(
            "Compare Company A and Company B for long-term growth."
        ),
        candidate_discovery_required=False,
        candidate_names=[
            "Company A",
            "Company B",
        ],
        comparison_criteria=[
            "revenue growth",
            "profitability",
            "valuation",
            "material risks",
        ],
        risk_categories=[
            "company-specific risk",
            "valuation risk",
        ],
        evidence_requirements=[requirement],
        search_queries=[query],
        preferred_source_categories=[
            SourceCategory.PRIMARY,
            SourceCategory.SECONDARY,
        ],
        candidate_limit=2,
        source_limit_per_candidate=5,
        assumptions=[],
    )


def create_planner(
    raw_result: object,
) -> ResearchPlanner:
    """Create a planner with a mocked smolagents run method."""

    planner = object.__new__(ResearchPlanner)
    planner.run = Mock(return_value=raw_result)

    return planner


def test_parse_research_plan_accepts_model() -> None:
    """Existing ResearchPlan should be returned unchanged."""

    expected_plan = create_research_plan(uuid4())

    parsed_plan = ResearchPlanner._parse_research_plan(
        expected_plan
    )

    assert parsed_plan is expected_plan


def test_parse_research_plan_accepts_json() -> None:
    """JSON should reconstruct a ResearchPlan."""

    expected_plan = create_research_plan(uuid4())

    parsed_plan = ResearchPlanner._parse_research_plan(
        expected_plan.model_dump_json()
    )

    assert parsed_plan == expected_plan


def test_parse_research_plan_rejects_empty_result() -> None:
    """Empty planner output should be rejected."""

    with pytest.raises(
        ValueError,
        match="returned an empty research plan",
    ):
        ResearchPlanner._parse_research_plan("   ")


def test_parse_research_plan_rejects_invalid_json() -> None:
    """Non-JSON planner output should be rejected."""

    with pytest.raises(
        ValueError,
        match="did not return valid research-plan JSON",
    ):
        ResearchPlanner._parse_research_plan(
            "Not valid JSON."
        )


def test_create_research_plan_returns_valid_plan() -> None:
    """Complete intake should generate a validated plan."""

    workflow_id = uuid4()
    intake_result = create_complete_intake(workflow_id)
    expected_plan = create_research_plan(workflow_id)

    planner = create_planner(
        expected_plan.model_dump_json()
    )

    result = planner.create_research_plan(
        intake_result=intake_result
    )

    assert result == expected_plan
    planner.run.assert_called_once()


def test_create_research_plan_stops_incomplete_intake() -> None:
    """Incomplete intake must stop before model execution."""

    planner = create_planner(raw_result="")

    with pytest.raises(ClarificationRequiredError):
        planner.create_research_plan(
            intake_result=create_incomplete_intake(
                uuid4()
            )
        )

    planner.run.assert_not_called()


def test_plan_rejects_wrong_workflow() -> None:
    """ResearchPlan must belong to the intake workflow."""

    intake_result = create_complete_intake(uuid4())
    returned_plan = create_research_plan(uuid4())

    planner = create_planner(
        returned_plan.model_dump_json()
    )

    with pytest.raises(
        ValueError,
        match="workflow_id does not match",
    ):
        planner.create_research_plan(
            intake_result=intake_result
        )


def test_plan_rejects_changed_candidate_limit() -> None:
    """ResearchPlan must preserve the intake candidate limit."""

    workflow_id = uuid4()
    intake_result = create_complete_intake(workflow_id)
    returned_plan = create_research_plan(workflow_id)

    returned_plan = returned_plan.model_copy(
        update={
            "candidate_limit": 3,
        }
    )

    planner = create_planner(
        returned_plan.model_dump_json()
    )

    with pytest.raises(
        ValueError,
        match="candidate_limit does not match",
    ):
        planner.create_research_plan(
            intake_result=intake_result
        )


def test_plan_preserves_named_candidates() -> None:
    """ResearchPlan must preserve explicitly named candidates."""

    workflow_id = uuid4()
    intake_result = create_complete_intake(workflow_id)
    returned_plan = create_research_plan(workflow_id)

    returned_plan = returned_plan.model_copy(
        update={
            "candidate_names": ["Company A"],
        }
    )

    planner = create_planner(
        returned_plan.model_dump_json()
    )

    with pytest.raises(
        ValueError,
        match="did not preserve all explicitly named candidates",
    ):
        planner.create_research_plan(
            intake_result=intake_result
        )


def test_plan_rejects_excluded_candidate() -> None:
    """ResearchPlan cannot include an excluded candidate."""

    workflow_id = uuid4()
    intake_result = create_complete_intake(workflow_id)
    returned_plan = create_research_plan(workflow_id)

    returned_plan = returned_plan.model_copy(
        update={
            "candidate_names": [
                "Company A",
                "Company B",
                "Company C",
            ],
            "candidate_limit": 3,
        }
    )

    intake_result.research_scope.candidate_limit = 3

    planner = create_planner(
        returned_plan.model_dump_json()
    )

    with pytest.raises(
        ValueError,
        match="includes a candidate excluded",
    ):
        planner.create_research_plan(
            intake_result=intake_result
        )


def test_plan_rejects_excessive_source_limit() -> None:
    """ResearchPlan must respect the approved source limit."""

    workflow_id = uuid4()
    intake_result = create_complete_intake(workflow_id)
    returned_plan = create_research_plan(workflow_id)

    returned_plan = returned_plan.model_copy(
        update={
            "source_limit_per_candidate": 8,
        }
    )

    planner = create_planner(
        returned_plan.model_dump_json()
    )

    with pytest.raises(
        ValueError,
        match="exceeds the approved source limit",
    ):
        planner.create_research_plan(
            intake_result=intake_result
        )