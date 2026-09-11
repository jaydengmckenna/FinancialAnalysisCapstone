"""Tests for research-planning data contracts."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fin_automation.models.common import (
    SearchPurpose,
    SourceCategory,
    WorkflowStage,
)
from fin_automation.models.research import (
    AdditionalResearchRequest,
    EvidenceRequirement,
    ResearchPlan,
    SearchQuery,
)


def create_evidence_requirement(
    purpose: SearchPurpose,
    candidate_name: str | None = "Company A",
) -> EvidenceRequirement:
    """Create a valid evidence requirement for testing."""

    return EvidenceRequirement(
        name=f"{purpose.value} evidence",
        description=(
            "Collect evidence required for candidate analysis."
        ),
        candidate_name=candidate_name,
        search_purpose=purpose,
        preferred_source_categories=[
            SourceCategory.PRIMARY,
            SourceCategory.SECONDARY,
        ],
        required=True,
    )


def create_search_query(
    requirement: EvidenceRequirement,
) -> SearchQuery:
    """Create a valid search query for an evidence requirement."""

    return SearchQuery(
        query=(
            f"{requirement.candidate_name or 'candidate'} "
            f"{requirement.search_purpose.value}"
        ),
        purpose=requirement.search_purpose,
        candidate_name=requirement.candidate_name,
        evidence_requirement_ids=[
            requirement.requirement_id
        ],
    )


def create_valid_research_plan(
    workflow_id: UUID,
) -> ResearchPlan:
    """Create a valid research plan for testing."""

    growth_requirement = create_evidence_requirement(
        SearchPurpose.FINANCIAL_GROWTH
    )
    risk_requirement = create_evidence_requirement(
        SearchPurpose.RISK_RESEARCH
    )

    return ResearchPlan(
        workflow_id=workflow_id,
        research_objective=(
            "Compare Company A using financial and risk evidence."
        ),
        candidate_discovery_required=False,
        candidate_names=["Company A"],
        comparison_criteria=[
            "financial growth",
            "risk profile",
        ],
        risk_categories=[
            "company-specific risk",
        ],
        evidence_requirements=[
            growth_requirement,
            risk_requirement,
        ],
        search_queries=[
            create_search_query(growth_requirement),
            create_search_query(risk_requirement),
        ],
        preferred_source_categories=[
            SourceCategory.PRIMARY,
            SourceCategory.SECONDARY,
        ],
        candidate_limit=3,
        source_limit_per_candidate=5,
        assumptions=[],
    )


def test_evidence_requirement_accepts_valid_data() -> None:
    """A valid evidence requirement should be created."""

    requirement = create_evidence_requirement(
        SearchPurpose.PROFITABILITY
    )

    assert requirement.name == "profitability evidence"
    assert requirement.search_purpose == SearchPurpose.PROFITABILITY
    assert requirement.required is True
    assert requirement.requirement_id is not None


def test_evidence_requirement_rejects_empty_source_categories() -> None:
    """Evidence requirements need a preferred source category."""

    with pytest.raises(ValidationError):
        EvidenceRequirement(
            name="Profitability evidence",
            description="Collect profitability evidence.",
            search_purpose=SearchPurpose.PROFITABILITY,
            preferred_source_categories=[],
        )


def test_search_query_accepts_valid_data() -> None:
    """A valid search query should be created."""

    requirement = create_evidence_requirement(
        SearchPurpose.VALUATION
    )
    search_query = create_search_query(requirement)

    assert search_query.purpose == SearchPurpose.VALUATION
    assert search_query.evidence_requirement_ids == [
        requirement.requirement_id
    ]


def test_search_query_rejects_duplicate_requirement_ids() -> None:
    """A query should not repeat evidence references."""

    requirement_id = uuid4()

    with pytest.raises(
        ValidationError,
        match=(
            "Search-query evidence_requirement_ids "
            "must be unique"
        ),
    ):
        SearchQuery(
            query="Company A valuation",
            purpose=SearchPurpose.VALUATION,
            evidence_requirement_ids=[
                requirement_id,
                requirement_id,
            ],
        )


def test_additional_research_request_accepts_valid_data() -> None:
    """A valid additional-research request should be created."""

    request = AdditionalResearchRequest(
        workflow_id=uuid4(),
        requested_by_stage=WorkflowStage.FINANCIAL_ANALYSIS,
        candidate_name="Company A",
        missing_evidence="Current debt information",
        reason=(
            "Debt evidence is required for candidate comparison."
        ),
        suggested_search_purpose=SearchPurpose.BALANCE_SHEET,
        blocks_recommendation=True,
    )

    assert request.blocks_recommendation is True
    assert (
        request.requested_by_stage
        == WorkflowStage.FINANCIAL_ANALYSIS
    )
    assert request.created_at.tzinfo is not None
    assert request.created_at.utcoffset() is not None


def test_additional_research_request_rejects_blank_reason() -> None:
    """Additional research requests require a reason."""

    with pytest.raises(ValidationError):
        AdditionalResearchRequest(
            workflow_id=uuid4(),
            requested_by_stage=WorkflowStage.SOURCE_SELECTION,
            missing_evidence="Profitability evidence",
            reason="   ",
            suggested_search_purpose=SearchPurpose.PROFITABILITY,
        )


def test_additional_research_request_rejects_naive_datetime() -> None:
    """Additional research timestamps must be timezone-aware."""

    with pytest.raises(
        ValidationError,
        match="created_at must be timezone-aware",
    ):
        AdditionalResearchRequest(
            workflow_id=uuid4(),
            requested_by_stage=WorkflowStage.SOURCE_SELECTION,
            missing_evidence="Profitability evidence",
            reason="The current source does not contain the metric.",
            suggested_search_purpose=SearchPurpose.PROFITABILITY,
            created_at=datetime(2026, 9, 11, 9, 0, 0),
        )


def test_research_plan_accepts_valid_data() -> None:
    """A valid research plan should be created."""

    workflow_id = uuid4()
    plan = create_valid_research_plan(workflow_id)

    assert plan.workflow_id == workflow_id
    assert plan.candidate_names == ["Company A"]
    assert len(plan.evidence_requirements) == 2
    assert len(plan.search_queries) == 2
    assert plan.created_at.tzinfo is not None
    assert plan.created_at.utcoffset() is not None


def test_research_plan_rejects_blank_objective() -> None:
    """A research plan requires a meaningful objective."""

    workflow_id = uuid4()

    with pytest.raises(ValidationError):
        ResearchPlan(
            workflow_id=workflow_id,
            research_objective="   ",
            candidate_discovery_required=False,
            candidate_names=["Company A"],
            comparison_criteria=["financial growth"],
            evidence_requirements=[
                create_evidence_requirement(
                    SearchPurpose.FINANCIAL_GROWTH
                )
            ],
            search_queries=[],
            preferred_source_categories=[
                SourceCategory.PRIMARY
            ],
        )


def test_research_plan_rejects_duplicate_requirement_ids() -> None:
    """Evidence-requirement identifiers must be unique."""

    requirement = create_evidence_requirement(
        SearchPurpose.FINANCIAL_GROWTH
    )
    duplicate_requirement = requirement.model_copy(deep=True)

    with pytest.raises(
        ValidationError,
        match=(
            "Evidence-requirement identifiers must be unique"
        ),
    ):
        ResearchPlan(
            workflow_id=uuid4(),
            research_objective="Analyze Company A.",
            candidate_discovery_required=False,
            candidate_names=["Company A"],
            comparison_criteria=["financial growth"],
            evidence_requirements=[
                requirement,
                duplicate_requirement,
            ],
            search_queries=[
                create_search_query(requirement)
            ],
            preferred_source_categories=[
                SourceCategory.PRIMARY
            ],
        )


def test_research_plan_rejects_unknown_requirement_reference() -> None:
    """Query references must resolve within the research plan."""

    requirement = create_evidence_requirement(
        SearchPurpose.VALUATION
    )

    search_query = SearchQuery(
        query="Company A valuation",
        purpose=SearchPurpose.VALUATION,
        candidate_name="Company A",
        evidence_requirement_ids=[uuid4()],
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Every search-query evidence reference must "
            "resolve to an evidence requirement in the plan"
        ),
    ):
        ResearchPlan(
            workflow_id=uuid4(),
            research_objective="Analyze Company A valuation.",
            candidate_discovery_required=False,
            candidate_names=["Company A"],
            comparison_criteria=["valuation"],
            evidence_requirements=[requirement],
            search_queries=[search_query],
            preferred_source_categories=[
                SourceCategory.PRIMARY
            ],
        )


def test_research_plan_rejects_duplicate_candidate_names() -> None:
    """Candidate names should be unique without regard to case."""

    requirement = create_evidence_requirement(
        SearchPurpose.PROFITABILITY
    )

    with pytest.raises(
        ValidationError,
        match="Candidate names must be unique",
    ):
        ResearchPlan(
            workflow_id=uuid4(),
            research_objective="Compare candidates.",
            candidate_discovery_required=False,
            candidate_names=[
                "Company A",
                "company a",
            ],
            comparison_criteria=["profitability"],
            evidence_requirements=[requirement],
            search_queries=[
                create_search_query(requirement)
            ],
            preferred_source_categories=[
                SourceCategory.PRIMARY
            ],
        )


def test_research_plan_rejects_too_many_candidates() -> None:
    """Candidate names cannot exceed the approved limit."""

    requirement = create_evidence_requirement(
        SearchPurpose.PROFITABILITY,
        candidate_name=None,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "The number of candidate names cannot exceed "
            "candidate_limit"
        ),
    ):
        ResearchPlan(
            workflow_id=uuid4(),
            research_objective="Compare candidates.",
            candidate_discovery_required=False,
            candidate_names=[
                "Company A",
                "Company B",
                "Company C",
            ],
            comparison_criteria=["profitability"],
            evidence_requirements=[requirement],
            search_queries=[
                create_search_query(requirement)
            ],
            preferred_source_categories=[
                SourceCategory.PRIMARY
            ],
            candidate_limit=2,
        )


def test_research_plan_requires_names_without_discovery() -> None:
    """Named candidates are required when discovery is disabled."""

    requirement = create_evidence_requirement(
        SearchPurpose.PROFITABILITY,
        candidate_name=None,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "candidate_names are required when candidate "
            "discovery is not required"
        ),
    ):
        ResearchPlan(
            workflow_id=uuid4(),
            research_objective="Analyze candidates.",
            candidate_discovery_required=False,
            candidate_names=[],
            comparison_criteria=["profitability"],
            evidence_requirements=[requirement],
            search_queries=[
                create_search_query(requirement)
            ],
            preferred_source_categories=[
                SourceCategory.PRIMARY
            ],
        )


def test_research_plan_allows_empty_names_for_discovery() -> None:
    """Candidate discovery may begin without named candidates."""

    requirement = create_evidence_requirement(
        SearchPurpose.CANDIDATE_DISCOVERY,
        candidate_name=None,
    )

    plan = ResearchPlan(
        workflow_id=uuid4(),
        research_objective="Discover public-stock candidates.",
        candidate_discovery_required=True,
        candidate_names=[],
        comparison_criteria=["investor-profile alignment"],
        evidence_requirements=[requirement],
        search_queries=[
            create_search_query(requirement)
        ],
        preferred_source_categories=[
            SourceCategory.PRIMARY,
            SourceCategory.SECONDARY,
        ],
    )

    assert plan.candidate_discovery_required is True
    assert plan.candidate_names == []


def test_research_plan_rejects_unsupported_preferred_source() -> None:
    """Unsupported sources cannot be preferred."""

    requirement = create_evidence_requirement(
        SearchPurpose.PROFITABILITY
    )

    with pytest.raises(
        ValidationError,
        match="Unsupported sources cannot be preferred",
    ):
        ResearchPlan(
            workflow_id=uuid4(),
            research_objective="Analyze Company A.",
            candidate_discovery_required=False,
            candidate_names=["Company A"],
            comparison_criteria=["profitability"],
            evidence_requirements=[requirement],
            search_queries=[
                create_search_query(requirement)
            ],
            preferred_source_categories=[
                SourceCategory.UNSUPPORTED
            ],
        )


def test_research_plan_requires_matching_query_purpose() -> None:
    """A query purpose must match a referenced requirement."""

    requirement = create_evidence_requirement(
        SearchPurpose.PROFITABILITY
    )

    search_query = SearchQuery(
        query="Company A valuation",
        purpose=SearchPurpose.VALUATION,
        candidate_name="Company A",
        evidence_requirement_ids=[
            requirement.requirement_id
        ],
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Each search query must reference at least one "
            "evidence requirement with the same purpose"
        ),
    ):
        ResearchPlan(
            workflow_id=uuid4(),
            research_objective="Analyze Company A.",
            candidate_discovery_required=False,
            candidate_names=["Company A"],
            comparison_criteria=["profitability"],
            evidence_requirements=[requirement],
            search_queries=[search_query],
            preferred_source_categories=[
                SourceCategory.PRIMARY
            ],
        )