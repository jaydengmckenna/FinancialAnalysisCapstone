"""Focused offline tests for the Source Selection Agent boundary."""

from unittest.mock import Mock
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


class _StubTavilyTool:
    """Stand-in for the real TavilySearchTool — no network, no LLM."""

    def __init__(self) -> None:
        self.reset_results_called = False

    def reset_results(self) -> None:
        self.reset_results_called = True


class _StubSubmissionTool:
    """Stand-in for SubmitSourceSelectionTool.

    The real tool's `last_selection` is set as a side effect of the
    LLM calling `submit_source_selection` during `self.run(...)`.
    Since `self.run()` itself is mocked out below (no real LLM call
    happens), this stub lets the test control that side effect
    directly instead — exactly what `last_selection` would hold after
    a real run, without needing a real model.
    """

    def __init__(self, selection: SourceSelection | None) -> None:
        self.last_selection = selection
        self.reset_called = False

    def reset(self) -> None:
        self.reset_called = True


def make_agent_with_submitted_selection(
    selection: SourceSelection | None,
) -> SourceSelectionAgent:
    """Build an agent whose .run() never calls a real LLM.

    `object.__new__` skips `SourceSelectionAgent.__init__` (which
    would otherwise require a real smolagents Model), then the tool
    attributes `search_and_select` actually touches are replaced with
    lightweight stubs.
    """

    agent = object.__new__(SourceSelectionAgent)
    agent._tavily_search_tool = _StubTavilyTool()
    agent._submission_tool = _StubSubmissionTool(selection)
    agent.run = Mock(return_value="ignored — the result comes from the tool")
    return agent


def test_search_and_select_returns_the_submitted_selection() -> None:
    """The selection the (simulated) LLM submitted via its tool call
    should come back out, and both tools should be reset before the
    run — the actual return value of .run() is never used."""

    research_plan, requirement = make_plan()
    selection = SourceSelection(
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
    agent = make_agent_with_submitted_selection(selection)

    result = agent.search_and_select(research_plan=research_plan)

    assert result == selection
    assert agent._tavily_search_tool.reset_results_called is True
    assert agent._submission_tool.reset_called is True
    agent.run.assert_called_once()


def test_search_and_select_raises_when_agent_never_submits() -> None:
    """If the simulated LLM run finishes without ever calling
    submit_source_selection, that must be a clear, caught failure —
    not a silent empty result. This is a real failure mode observed
    live during Phase 9 QA, not a hypothetical one."""

    research_plan, _requirement = make_plan()
    agent = make_agent_with_submitted_selection(None)

    with pytest.raises(
        ValueError,
        match="completed without calling",
    ):
        agent.search_and_select(research_plan=research_plan)
