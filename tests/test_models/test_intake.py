"""Tests for intake data contracts."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

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


def create_research_request(
    workflow_id: UUID,
) -> ResearchRequest:
    """Create a valid research request for testing."""

    return ResearchRequest(
        workflow_id=workflow_id,
        original_prompt=(
            "Compare three foreign stocks for a high-risk investor "
            "seeking long-term growth."
        ),
        research_question=(
            "Compare foreign public stocks for long-term growth."
        ),
        request_type=RequestType.CANDIDATE_COMPARISON,
    )


def create_complete_investor_profile(
    workflow_id: UUID,
) -> InvestorProfile:
    """Create a valid and complete investor profile for testing."""

    return InvestorProfile(
        workflow_id=workflow_id,
        risk_tolerance=RiskTolerance.HIGH,
        investment_objective=InvestmentObjective.GROWTH,
        time_horizon=TimeHorizon.LONG_TERM,
        growth_or_income_preference="growth",
        geographic_preferences=["international"],
        industry_preferences=["technology"],
        excluded_regions=[],
        excluded_industries=["tobacco"],
        explicit_constraints=[],
    )


def create_research_scope(
    workflow_id: UUID,
) -> ResearchScope:
    """Create a valid research scope for testing."""

    return ResearchScope(
        workflow_id=workflow_id,
        asset_types=[AssetType.PUBLIC_STOCK],
        candidate_limit=3,
        geographic_scope=["international"],
        excluded_candidates=[],
    )


def test_research_request_accepts_valid_data() -> None:
    """A valid research request should be created successfully."""

    workflow_id = uuid4()

    request = create_research_request(workflow_id)

    assert request.workflow_id == workflow_id
    assert request.request_type == RequestType.CANDIDATE_COMPARISON
    assert request.original_prompt.startswith("Compare three")
    assert request.research_question.startswith("Compare foreign")
    assert request.request_id is not None
    assert request.created_at.tzinfo is not None
    assert request.created_at.utcoffset() is not None


def test_research_request_strips_surrounding_whitespace() -> None:
    """Text fields should have surrounding whitespace removed."""

    request = ResearchRequest(
        workflow_id=uuid4(),
        original_prompt="  Analyze Company A.  ",
        research_question="  Analyze Company A.  ",
        request_type=RequestType.SINGLE_CANDIDATE_ANALYSIS,
    )

    assert request.original_prompt == "Analyze Company A."
    assert request.research_question == "Analyze Company A."


@pytest.mark.parametrize(
    "field_name",
    [
        "original_prompt",
        "research_question",
    ],
)
def test_research_request_rejects_blank_text(
    field_name: str,
) -> None:
    """Required text fields should reject whitespace-only values."""

    request_data = {
        "workflow_id": uuid4(),
        "original_prompt": "Analyze Company A.",
        "research_question": "Analyze Company A.",
        "request_type": RequestType.SINGLE_CANDIDATE_ANALYSIS,
    }

    request_data[field_name] = "   "

    with pytest.raises(ValidationError):
        ResearchRequest(**request_data)


def test_research_request_rejects_invalid_request_type() -> None:
    """The request type must use an approved enum value."""

    with pytest.raises(ValidationError):
        ResearchRequest(
            workflow_id=uuid4(),
            original_prompt="Find an investment.",
            research_question="Find an investment.",
            request_type="unsupported_request_type",
        )


def test_research_request_rejects_naive_datetime() -> None:
    """The request timestamp must contain timezone information."""

    with pytest.raises(
        ValidationError,
        match="created_at must be timezone-aware",
    ):
        ResearchRequest(
            workflow_id=uuid4(),
            original_prompt="Analyze Company A.",
            research_question="Analyze Company A.",
            request_type=RequestType.SINGLE_CANDIDATE_ANALYSIS,
            created_at=datetime(2026, 9, 10, 12, 0, 0),
        )


def test_intake_models_reject_unknown_fields() -> None:
    """Intake models should reject undocumented fields."""

    with pytest.raises(ValidationError):
        ResearchRequest(
            workflow_id=uuid4(),
            original_prompt="Analyze Company A.",
            research_question="Analyze Company A.",
            request_type=RequestType.SINGLE_CANDIDATE_ANALYSIS,
            unsupported_field="unexpected value",
        )


def test_investor_profile_accepts_valid_preferences() -> None:
    """A valid investor profile should be created successfully."""

    workflow_id = uuid4()

    profile = create_complete_investor_profile(workflow_id)

    assert profile.workflow_id == workflow_id
    assert profile.risk_tolerance == RiskTolerance.HIGH
    assert profile.investment_objective == InvestmentObjective.GROWTH
    assert profile.time_horizon == TimeHorizon.LONG_TERM
    assert profile.excluded_industries == ["tobacco"]


def test_investor_profile_allows_missing_preferences() -> None:
    """Missing preferences should remain absent before clarification."""

    profile = InvestorProfile(
        workflow_id=uuid4(),
    )

    assert profile.risk_tolerance is None
    assert profile.investment_objective is None
    assert profile.time_horizon is None


def test_investor_profile_rejects_overlapping_regions() -> None:
    """A region cannot be both preferred and excluded."""

    with pytest.raises(
        ValidationError,
        match=(
            "Geographic preferences and excluded regions "
            "must not overlap"
        ),
    ):
        InvestorProfile(
            workflow_id=uuid4(),
            geographic_preferences=["Europe"],
            excluded_regions=["europe"],
        )


def test_investor_profile_rejects_overlapping_industries() -> None:
    """An industry cannot be both preferred and excluded."""

    with pytest.raises(
        ValidationError,
        match=(
            "Industry preferences and excluded industries "
            "must not overlap"
        ),
    ):
        InvestorProfile(
            workflow_id=uuid4(),
            industry_preferences=["Technology"],
            excluded_industries=["technology"],
        )


def test_research_scope_uses_expected_defaults() -> None:
    """Research scope should use bounded initial defaults."""

    scope = ResearchScope(
        workflow_id=uuid4(),
    )

    assert scope.asset_types == [AssetType.PUBLIC_STOCK]
    assert scope.candidate_limit == 3
    assert scope.named_candidates == []
    assert scope.excluded_candidates == []


@pytest.mark.parametrize(
    "candidate_limit",
    [
        0,
        4,
    ],
)
def test_research_scope_rejects_invalid_candidate_limit(
    candidate_limit: int,
) -> None:
    """Candidate limits outside one through three should fail."""

    with pytest.raises(ValidationError):
        ResearchScope(
            workflow_id=uuid4(),
            candidate_limit=candidate_limit,
        )


def test_research_scope_rejects_empty_asset_types() -> None:
    """At least one supported asset type must be present."""

    with pytest.raises(ValidationError):
        ResearchScope(
            workflow_id=uuid4(),
            asset_types=[],
        )


def test_research_scope_rejects_unsupported_asset_type() -> None:
    """Unsupported financial instruments should be rejected."""

    with pytest.raises(ValidationError):
        ResearchScope(
            workflow_id=uuid4(),
            asset_types=["cryptocurrency"],
        )


def test_research_scope_rejects_overlapping_candidates() -> None:
    """A candidate cannot be both included and excluded."""

    with pytest.raises(
        ValidationError,
        match=(
            "Named candidates and excluded candidates "
            "must not overlap"
        ),
    ):
        ResearchScope(
            workflow_id=uuid4(),
            named_candidates=["Company A"],
            excluded_candidates=["company a"],
        )


def test_research_scope_rejects_too_many_named_candidates() -> None:
    """Named candidates cannot exceed the candidate limit."""

    with pytest.raises(
        ValidationError,
        match=(
            "The number of named candidates cannot exceed "
            "candidate_limit"
        ),
    ):
        ResearchScope(
            workflow_id=uuid4(),
            candidate_limit=2,
            named_candidates=[
                "Company A",
                "Company B",
                "Company C",
            ],
        )


def test_complete_intake_result_can_proceed_without_clarification() -> None:
    """Complete intake should not require user clarification."""

    workflow_id = uuid4()

    intake_result = IntakeResult(
        workflow_id=workflow_id,
        research_request=create_research_request(workflow_id),
        investor_profile=create_complete_investor_profile(
            workflow_id
        ),
        research_scope=create_research_scope(workflow_id),
        assumptions=[],
        missing_fields=[],
        requires_clarification=False,
        clarification_questions=[],
    )

    assert intake_result.workflow_id == workflow_id
    assert intake_result.requires_clarification is False
    assert intake_result.missing_fields == []
    assert intake_result.created_at.tzinfo is not None
    assert intake_result.created_at.utcoffset() is not None


def test_incomplete_intake_result_requires_clarification() -> None:
    """Missing required profile fields should support clarification."""

    workflow_id = uuid4()

    intake_result = IntakeResult(
        workflow_id=workflow_id,
        research_request=create_research_request(workflow_id),
        investor_profile=InvestorProfile(
            workflow_id=workflow_id,
            risk_tolerance=RiskTolerance.HIGH,
            investment_objective=None,
            time_horizon=None,
        ),
        research_scope=create_research_scope(workflow_id),
        missing_fields=[
            "investment_objective",
            "time_horizon",
        ],
        requires_clarification=True,
        clarification_questions=[
            "What is the primary investment objective?",
            "What is the intended investment time horizon?",
        ],
    )

    assert intake_result.requires_clarification is True
    assert set(intake_result.missing_fields) == {
        "investment_objective",
        "time_horizon",
    }


def test_intake_result_rejects_mismatched_workflow_ids() -> None:
    """Nested intake records must belong to one workflow."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match=(
            "All intake records must use the same workflow_id"
        ),
    ):
        IntakeResult(
            workflow_id=workflow_id,
            research_request=create_research_request(workflow_id),
            investor_profile=create_complete_investor_profile(
                uuid4()
            ),
            research_scope=create_research_scope(workflow_id),
            missing_fields=[],
            requires_clarification=False,
            clarification_questions=[],
        )


def test_intake_result_rejects_inaccurate_missing_fields() -> None:
    """Missing-field records must match the actual missing values."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match=(
            "missing_fields must exactly identify the missing "
            "required investor-profile fields"
        ),
    ):
        IntakeResult(
            workflow_id=workflow_id,
            research_request=create_research_request(workflow_id),
            investor_profile=InvestorProfile(
                workflow_id=workflow_id,
                risk_tolerance=RiskTolerance.HIGH,
                investment_objective=None,
                time_horizon=None,
            ),
            research_scope=create_research_scope(workflow_id),
            missing_fields=["investment_objective"],
            requires_clarification=True,
            clarification_questions=[
                "What is the primary investment objective?",
            ],
        )


def test_intake_result_rejects_missing_fields_without_clarification() -> None:
    """Missing required fields must stop the workflow for clarification."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match=(
            "requires_clarification must be true when required "
            "investor-profile fields are missing"
        ),
    ):
        IntakeResult(
            workflow_id=workflow_id,
            research_request=create_research_request(workflow_id),
            investor_profile=InvestorProfile(
                workflow_id=workflow_id,
            ),
            research_scope=create_research_scope(workflow_id),
            missing_fields=[
                "risk_tolerance",
                "investment_objective",
                "time_horizon",
            ],
            requires_clarification=False,
            clarification_questions=[],
        )


def test_intake_result_requires_clarification_questions() -> None:
    """Clarification status requires at least one question."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match=(
            "Clarification requires at least one question"
        ),
    ):
        IntakeResult(
            workflow_id=workflow_id,
            research_request=create_research_request(workflow_id),
            investor_profile=InvestorProfile(
                workflow_id=workflow_id,
            ),
            research_scope=create_research_scope(workflow_id),
            missing_fields=[
                "risk_tolerance",
                "investment_objective",
                "time_horizon",
            ],
            requires_clarification=True,
            clarification_questions=[],
        )


def test_complete_intake_rejects_unnecessary_clarification_questions() -> None:
    """Complete intake should not contain clarification questions."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match=(
            "Clarification questions must be empty when "
            "clarification is not required"
        ),
    ):
        IntakeResult(
            workflow_id=workflow_id,
            research_request=create_research_request(workflow_id),
            investor_profile=create_complete_investor_profile(
                workflow_id
            ),
            research_scope=create_research_scope(workflow_id),
            missing_fields=[],
            requires_clarification=False,
            clarification_questions=[
                "This question should not be present.",
            ],
        )