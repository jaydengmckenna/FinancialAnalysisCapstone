"""Tests for deterministic SourceRecord construction."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from fin_automation.agents.evidence_extraction import EvidenceExtractionAgent
from fin_automation.models.common import SearchPurpose, SourceCategory
from fin_automation.models.research import EvidenceRequirement
from fin_automation.models.sources import ExtractedEvidence, SelectedSource


def create_selected_source(
    raw_content: str | None = "Reported source content.",
    requirement_id=None,
):
    return SelectedSource(
        search_result_id=uuid4(),
        url="https://example.com/results",
        title="Company A Results",
        domain="example.com",
        raw_content=raw_content,
        candidate_name="Company A",
        selected=True,
        expected_source_category=SourceCategory.PRIMARY,
        selection_reason="Relevant primary source.",
        exclusion_reason=None,
        evidence_requirement_ids=[requirement_id or uuid4()],
    )


def test_build_source_record_preserves_selected_source() -> None:
    workflow_id = uuid4()
    selected = create_selected_source()

    source = EvidenceExtractionAgent._build_source_record(
        selected_source=selected,
        workflow_id=workflow_id,
    )

    assert source.workflow_id == workflow_id
    assert source.search_result_id == selected.search_result_id
    assert str(source.url) == str(selected.url)
    assert source.candidate_names == ["Company A"]


def test_build_source_record_requires_content() -> None:
    with pytest.raises(ValueError, match="requires selected source content"):
        EvidenceExtractionAgent._build_source_record(
            selected_source=create_selected_source(None),
            workflow_id=uuid4(),
        )


def make_requirement() -> EvidenceRequirement:
    return EvidenceRequirement(
        name="Revenue growth",
        description="Find revenue growth evidence.",
        candidate_name="Company A",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.PRIMARY],
        required=True,
    )


class _StubEvidenceSubmissionTool:
    """Stand-in for SubmitExtractedEvidenceTool.

    `accepted_evidence`/`evidence_gaps` are set as a side effect of
    the LLM calling `submit_extracted_evidence` during `self.run(...)`.
    Since `self.run()` is mocked below (no real LLM call happens),
    this stub lets the test control that side effect directly —
    exactly what those properties would hold after a real run.
    """

    def __init__(self, evidence: list[ExtractedEvidence], gaps: list[str]) -> None:
        self.accepted_evidence = evidence
        self.evidence_gaps = gaps
        self.begin_run_called_with: dict | None = None

    def begin_run(self, *, source_record, evidence_requirements) -> None:
        self.begin_run_called_with = {
            "source_record": source_record,
            "evidence_requirements": evidence_requirements,
        }


def make_agent_with_submitted_evidence(
    evidence: list[ExtractedEvidence],
    gaps: list[str],
) -> EvidenceExtractionAgent:
    """Build an agent whose .run() never calls a real LLM.

    `object.__new__` skips `EvidenceExtractionAgent.__init__` (which
    would otherwise require a real smolagents Model), then the tool
    attribute `extract_evidence` actually touches is replaced with a
    lightweight stub.
    """

    agent = object.__new__(EvidenceExtractionAgent)
    agent._submission_tool = _StubEvidenceSubmissionTool(evidence, gaps)
    agent.run = Mock(return_value="ignored — the result comes from the tool")
    return agent


def test_extract_evidence_returns_the_submitted_evidence() -> None:
    """The evidence the (simulated) LLM submitted via its tool call
    should come back out, and begin_run should have been called with
    the built SourceRecord and the matching requirement — the actual
    return value of .run() is never used."""

    requirement = make_requirement()
    selected_source = create_selected_source(
        requirement_id=requirement.requirement_id
    )
    workflow_id = uuid4()
    canned_evidence = [
        ExtractedEvidence(
            workflow_id=workflow_id,
            source_id=uuid4(),
            candidate_name="Company A",
            evidence_requirement_id=requirement.requirement_id,
            evidence_type="revenue",
            content="Company A revenue was 110 million in FY2025.",
        )
    ]
    agent = make_agent_with_submitted_evidence(
        evidence=canned_evidence,
        gaps=["Net income not found."],
    )

    source_record, evidence, gaps = agent.extract_evidence(
        selected_source=selected_source,
        evidence_requirements=[requirement],
        workflow_id=workflow_id,
    )

    assert evidence == canned_evidence
    assert gaps == ["Net income not found."]
    assert agent._submission_tool.begin_run_called_with is not None
    assert (
        agent._submission_tool.begin_run_called_with["source_record"]
        == source_record
    )
    agent.run.assert_called_once()


def test_extract_evidence_rejects_source_outside_extraction_scope() -> None:
    """A selected source citing an evidence requirement that wasn't
    approved for this extraction pass must be rejected before any
    (simulated) LLM call happens — not silently extracted anyway."""

    requirement = make_requirement()
    unrelated_requirement_id = uuid4()
    selected_source = create_selected_source(
        requirement_id=unrelated_requirement_id
    )
    agent = make_agent_with_submitted_evidence(evidence=[], gaps=[])

    with pytest.raises(
        ValueError,
        match="outside the supplied extraction scope",
    ):
        agent.extract_evidence(
            selected_source=selected_source,
            evidence_requirements=[requirement],
            workflow_id=uuid4(),
        )

    agent.run.assert_not_called()
