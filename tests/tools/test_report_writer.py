"""Focused tests for the agent-callable ReportWriterTool."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from fin_automation.models.financial import (
    CalculatedMetric,
    CandidateAnalysis,
    CategoryEvaluation,
    RecommendationResult,
)
from fin_automation.models.sources import ExtractedEvidence, SourceRecord
from fin_automation.models.validation import ValidationResult
from fin_automation.tools.report_writer import ReportWriterTool


VALID_MARKDOWN = """
# Research Question
Example question.

# Investor Profile
Example profile.

# Research Scope
Example scope.

# Executive Summary
Example summary.

# Research Methodology
Example methodology.

# Candidate Analyses
Example analysis.

# Candidate Comparison
Example comparison.

# Recommendation Outcome
Example outcome.

# Material Risks
Example risk.

# Missing Information and Unresolved Conflicts
None identified.

# Limitations
Example limitation.

# Sources
Example source.

# Human Review
Human review is required before use.
""".strip()


def make_context(tmp_path: Path):
    """Build one internally consistent workflow fixture for the tool."""

    workflow_id = uuid4()
    source_id = uuid4()
    evidence_id = uuid4()
    previous_evidence_id = uuid4()
    calculation_id = uuid4()
    analysis_id = uuid4()
    validation_id = uuid4()
    recommendation_id = uuid4()

    source_record = SourceRecord(
        source_id=source_id,
        workflow_id=workflow_id,
        search_result_id=uuid4(),
        title="Example source",
        url="https://example.com/report",
        retrieval_date=date.today(),
        source_category="primary",
        parsing_status="success",
        candidate_names=["Example Inc"],
        content_summary="Example content summary.",
    )
    evidence_record = ExtractedEvidence(
        evidence_id=evidence_id,
        workflow_id=workflow_id,
        source_id=source_id,
        candidate_name="Example Inc",
        evidence_type="revenue",
        content="Example Inc reported revenue of 100 million USD.",
        reported_value=Decimal("100"),
        currency="USD",
        unit="million",
        reporting_period="FY2024",
    )
    previous_evidence_record = ExtractedEvidence(
        evidence_id=previous_evidence_id,
        workflow_id=workflow_id,
        source_id=source_id,
        candidate_name="Example Inc",
        evidence_type="revenue",
        content="Example Inc reported revenue of 90 million USD.",
        reported_value=Decimal("90"),
        currency="USD",
        unit="million",
        reporting_period="FY2023",
    )
    calculation = CalculatedMetric(
        calculation_id=calculation_id,
        workflow_id=workflow_id,
        operation="difference",
        metric_name="revenue difference",
        candidate_names=["Example Inc"],
        value=Decimal("10.00"),
        input_evidence_ids=[evidence_id, previous_evidence_id],
        formula="first - second",
    )
    category_evaluation = CategoryEvaluation(
        workflow_id=workflow_id,
        candidate_name="Example Inc",
        category_name="financial_performance",
        availability_status="available",
        score=Decimal("75"),
        calculation_ids=[calculation_id],
        rationale="Backed by a completed calculation.",
        confidence="moderate",
    )
    candidate_analysis = CandidateAnalysis(
        analysis_id=analysis_id,
        workflow_id=workflow_id,
        candidate_name="Example Inc",
        status="completed",
        category_evaluations=[category_evaluation],
        calculation_ids=[calculation_id],
        supporting_evidence_ids=[evidence_id, previous_evidence_id],
        confidence="moderate",
        rationale="Supported by extracted evidence.",
    )
    recommendation_result = RecommendationResult(
        recommendation_id=recommendation_id,
        workflow_id=workflow_id,
        outcome="qualified_recommendation",
        preferred_candidate="Example Inc",
        ranked_candidates=["Example Inc"],
        candidate_analysis_ids=[analysis_id],
        material_risks=["Example risk."],
        rationale="Example Inc appears aligned for further research.",
        confidence="moderate",
    )
    validation_result = ValidationResult(
        validation_id=validation_id,
        workflow_id=workflow_id,
        recommendation_id=recommendation_id,
        outcome="approved",
        approved_candidate_analysis_ids=[analysis_id],
        approved_source_ids=[source_id],
        approved_evidence_ids=[evidence_id, previous_evidence_id],
        approved_calculation_ids=[calculation_id],
        summary="Validated.",
    )

    tool = ReportWriterTool(output_directory=tmp_path)
    tool.begin_run(
        workflow_id=workflow_id,
        validation_result=validation_result,
        recommendation_result=recommendation_result,
        source_records=[source_record],
        evidence_records=[evidence_record, previous_evidence_record],
        calculations=[calculation],
        candidate_analyses=[candidate_analysis],
    )

    return {
        "tool": tool,
        "workflow_id": workflow_id,
        "source_id": source_id,
        "evidence_id": evidence_id,
        "previous_evidence_id": previous_evidence_id,
        "calculation_id": calculation_id,
        "analysis_id": analysis_id,
        "validation_id": validation_id,
        "recommendation_id": recommendation_id,
    }


def make_payload(context: dict[str, object]) -> dict[str, object]:
    """Build a valid agent-style payload referencing the fixture's ids."""

    return {
        "workflow_id": str(context["workflow_id"]),
        "validation_id": str(context["validation_id"]),
        "recommendation_id": str(context["recommendation_id"]),
        "report_type": "research_report",
        "recommendation_outcome": "qualified_recommendation",
        "preferred_candidate": "Example Inc",
        "title": "Example Inc research brief",
        "markdown_content": VALID_MARKDOWN,
        "risks": ["Example risk."],
        "limitations": ["Example limitation."],
        "human_review_statement": (
            "Human review is required before use."
        ),
        "candidate_analysis_ids": [str(context["analysis_id"])],
        "source_ids": [str(context["source_id"])],
        "evidence_ids": [
            str(context["evidence_id"]),
            str(context["previous_evidence_id"]),
        ],
        "calculation_ids": [str(context["calculation_id"])],
    }


def test_forward_requires_begin_run(tmp_path: Path) -> None:
    """Calling forward() before begin_run() should fail clearly."""

    tool = ReportWriterTool(output_directory=tmp_path)

    with pytest.raises(RuntimeError, match="begin_run"):
        tool.forward({"title": "Anything"})


def test_forward_writes_valid_payload(tmp_path: Path) -> None:
    """A valid agent payload should be written and the artifact stored."""

    context = make_context(tmp_path)
    payload = make_payload(context)

    result = context["tool"].forward(payload)

    assert "written" in result.casefold()
    assert context["tool"].last_artifact is not None
    written_path = tmp_path / context["tool"].last_artifact.file_name
    assert written_path.is_file()
    assert written_path.read_text(encoding="utf-8") == VALID_MARKDOWN


def test_forward_ignores_agent_supplied_identifiers(tmp_path: Path) -> None:
    """The agent's own report_draft_id/created_at must not be trusted."""

    context = make_context(tmp_path)
    payload = make_payload(context)
    payload["report_draft_id"] = "not-a-real-uuid"
    payload["created_at"] = "not-a-real-timestamp"

    context["tool"].forward(payload)

    assert context["tool"].last_artifact is not None


def test_forward_rejects_unapproved_evidence_id(tmp_path: Path) -> None:
    """A citation to evidence outside the approved set must be rejected."""

    context = make_context(tmp_path)
    payload = make_payload(context)
    payload["evidence_ids"] = [str(uuid4())]

    with pytest.raises(ValueError, match="unknown evidence_ids"):
        context["tool"].forward(payload)


def test_forward_rejects_mismatched_preferred_candidate(
    tmp_path: Path,
) -> None:
    """The draft must preserve the approved recommendation's candidate."""

    context = make_context(tmp_path)
    payload = make_payload(context)
    payload["preferred_candidate"] = "A Different Company"

    with pytest.raises(ValueError, match="preferred candidate"):
        context["tool"].forward(payload)


def test_forward_rejects_missing_required_section(tmp_path: Path) -> None:
    """Structural validation still applies to agent-submitted drafts."""

    context = make_context(tmp_path)
    payload = make_payload(context)
    payload["markdown_content"] = "# Research Question\nOnly one section."

    with pytest.raises(ValueError, match="missing required sections"):
        context["tool"].forward(payload)
