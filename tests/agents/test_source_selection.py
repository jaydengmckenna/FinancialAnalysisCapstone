"""Focused offline tests for the Source Selection Agent boundary."""

from uuid import uuid4

import pytest

from fin_automation.agents.source_selection import SourceSelectionAgent
from fin_automation.models.common import (
    SearchPurpose,
    SourceCategory,
    SourceSelectionStatus,
)
from fin_automation.models.research import (
    EvidenceRequirement,
    ResearchPlan,
    SearchQuery,
)
from fin_automation.models.sources import (
    SelectedSource,
    SourceSelection,
)


def make_plan() -> ResearchPlan:
    requirement = EvidenceRequirement(
        name="Revenue growth",
        description="Find revenue growth evidence.",
        candidate_name="Example Inc",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.PRIMARY],
        required=True,
    )
    return ResearchPlan(
        workflow_id=uuid4(),
        research_objective="Compare revenue growth.",
        candidate_discovery_required=False,
        candidate_names=["Example Inc"],
        comparison_criteria=["revenue growth"],
        risk_categories=["market competition"],
        evidence_requirements=[requirement],
        search_queries=[
            SearchQuery(
                query="Example Inc revenue growth",
                purpose=SearchPurpose.FINANCIAL_GROWTH,
                candidate_name="Example Inc",
                evidence_requirement_ids=[requirement.requirement_id],
            )
        ],
        preferred_source_categories=[SourceCategory.PRIMARY],
        candidate_limit=1,
        source_limit_per_candidate=3,
        assumptions=[],
    ), requirement


def make_selected_source(*, requirement_id, raw_content: str | None) -> SelectedSource:
    return SelectedSource(
        search_result_id=uuid4(),
        url="https://example.com/source",
        title="Example source",
        domain="example.com",
        raw_content=raw_content,
        candidate_name="Example Inc",
        selected=True,
        expected_source_category=SourceCategory.PRIMARY,
        selection_reason="Relevant to revenue growth.",
        evidence_requirement_ids=[requirement_id],
    )


def test_validate_source_selection_identity_accepts_source_with_raw_content() -> None:
    """A selected source with real Tavily raw content should pass."""

    research_plan, requirement = make_plan()
    source_selection = SourceSelection(
        workflow_id=research_plan.workflow_id,
        plan_id=research_plan.plan_id,
        status=SourceSelectionStatus.READY_FOR_RETRIEVAL,
        selections=[
            make_selected_source(
                requirement_id=requirement.requirement_id,
                raw_content="Real retrieved page content.",
            )
        ],
        uncovered_evidence_requirement_ids=[],
        additional_research_requests=[],
    )

    SourceSelectionAgent._validate_source_selection_identity(
        source_selection, research_plan
    )


def test_validate_source_selection_identity_rejects_source_without_raw_content() -> None:
    """A selected source with no Tavily raw content must be rejected.

    This is the actual failure mode behind "a webpage cannot be
    retrieved" now that retrieval is Tavily-only: there is no separate
    HTTP fetch to fail, but a selected search result can still lack
    raw_content, and that must not silently proceed to extraction.
    """

    research_plan, requirement = make_plan()
    source_selection = SourceSelection(
        workflow_id=research_plan.workflow_id,
        plan_id=research_plan.plan_id,
        status=SourceSelectionStatus.READY_FOR_RETRIEVAL,
        selections=[
            make_selected_source(
                requirement_id=requirement.requirement_id,
                raw_content=None,
            )
        ],
        uncovered_evidence_requirement_ids=[],
        additional_research_requests=[],
    )

    with pytest.raises(
        ValueError,
        match="does not contain Tavily raw content",
    ):
        SourceSelectionAgent._validate_source_selection_identity(
            source_selection, research_plan
        )
