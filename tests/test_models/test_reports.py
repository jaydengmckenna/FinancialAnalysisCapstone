"""Tests for report and output-artifact data contracts."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fin_automation.models.common import (
    ArtifactStatus,
    ArtifactType,
    RecommendationOutcome,
    ReportType,
)
from fin_automation.models.reports import (
    ReportArtifact,
    ReportDraft,
    WorkflowArtifact,
)


def create_report_draft(
    workflow_id: UUID,
) -> ReportDraft:
    """Create a valid final research-report draft."""

    return ReportDraft(
        workflow_id=workflow_id,
        validation_id=uuid4(),
        recommendation_id=uuid4(),
        report_type=ReportType.RESEARCH_REPORT,
        recommendation_outcome=(
            RecommendationOutcome.RANKED_RECOMMENDATION
        ),
        preferred_candidate="Company A",
        title="Investment Research Report",
        markdown_content=(
            "# Investment Research Report\n\n"
            "Company A is the preferred research candidate."
        ),
        risks=["Market conditions may change."],
        limitations=[
            "The report relies on publicly available information."
        ],
        human_review_statement=(
            "This report requires human review before any decision."
        ),
        candidate_analysis_ids=[uuid4()],
        source_ids=[uuid4()],
        evidence_ids=[uuid4()],
        calculation_ids=[uuid4()],
    )


def create_markdown_artifact(
    workflow_id: UUID,
    report_draft_id: UUID,
) -> ReportArtifact:
    """Create a valid Markdown report artifact."""

    return ReportArtifact(
        workflow_id=workflow_id,
        report_draft_id=report_draft_id,
        artifact_type=ArtifactType.MARKDOWN_REPORT,
        status=ArtifactStatus.CREATED,
        file_name="investment_research_report.md",
        relative_path="outputs/investment_research_report.md",
        created_at=datetime.now(timezone.utc),
    )


def create_json_artifact(
    workflow_id: UUID,
    report_draft_id: UUID,
) -> ReportArtifact:
    """Create a valid JSON workflow artifact."""

    return ReportArtifact(
        workflow_id=workflow_id,
        report_draft_id=report_draft_id,
        artifact_type=ArtifactType.JSON_WORKFLOW,
        status=ArtifactStatus.CREATED,
        file_name="workflow_artifact.json",
        relative_path="outputs/workflow_artifact.json",
        created_at=datetime.now(timezone.utc),
    )


def test_report_draft_accepts_valid_data() -> None:
    """A complete report draft should pass validation."""

    workflow_id = uuid4()
    report = create_report_draft(workflow_id)

    assert report.workflow_id == workflow_id
    assert report.preferred_candidate == "Company A"
    assert report.report_type == ReportType.RESEARCH_REPORT
    assert report.created_at.tzinfo is not None


def test_report_draft_rejects_blank_title() -> None:
    """A report title cannot contain only whitespace."""

    workflow_id = uuid4()

    with pytest.raises(ValidationError):
        ReportDraft(
            workflow_id=workflow_id,
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=ReportType.RESEARCH_REPORT,
            recommendation_outcome=(
                RecommendationOutcome.RESEARCH_SHORTLIST
            ),
            title="   ",
            markdown_content="# Research Report",
            risks=["Market risk."],
            limitations=["Public information only."],
            human_review_statement=(
                "This report requires human review."
            ),
        )


def test_report_draft_requires_risks() -> None:
    """A report draft must include material risks."""

    with pytest.raises(ValidationError):
        ReportDraft(
            workflow_id=uuid4(),
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=ReportType.RESEARCH_REPORT,
            recommendation_outcome=(
                RecommendationOutcome.RESEARCH_SHORTLIST
            ),
            title="Investment Research Report",
            markdown_content="# Investment Research Report",
            risks=[],
            limitations=["Public information only."],
            human_review_statement=(
                "This report requires human review."
            ),
        )


def test_report_draft_requires_limitations() -> None:
    """A report draft must include limitations."""

    with pytest.raises(ValidationError):
        ReportDraft(
            workflow_id=uuid4(),
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=ReportType.RESEARCH_REPORT,
            recommendation_outcome=(
                RecommendationOutcome.RESEARCH_SHORTLIST
            ),
            title="Investment Research Report",
            markdown_content="# Investment Research Report",
            risks=["Market risk."],
            limitations=[],
            human_review_statement=(
                "This report requires human review."
            ),
        )


def test_report_draft_requires_human_review_language() -> None:
    """A report must explicitly preserve human-review authority."""

    with pytest.raises(
        ValidationError,
        match="explicit human-review statement",
    ):
        ReportDraft(
            workflow_id=uuid4(),
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=ReportType.RESEARCH_REPORT,
            recommendation_outcome=(
                RecommendationOutcome.RESEARCH_SHORTLIST
            ),
            title="Investment Research Report",
            markdown_content="# Investment Research Report",
            risks=["Market risk."],
            limitations=["Public information only."],
            human_review_statement=(
                "The report is informational."
            ),
        )


def test_ranked_report_requires_preferred_candidate() -> None:
    """A ranked report must identify its preferred candidate."""

    with pytest.raises(
        ValidationError,
        match="require a preferred candidate",
    ):
        ReportDraft(
            workflow_id=uuid4(),
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=ReportType.RESEARCH_REPORT,
            recommendation_outcome=(
                RecommendationOutcome.RANKED_RECOMMENDATION
            ),
            title="Investment Research Report",
            markdown_content="# Investment Research Report",
            risks=["Market risk."],
            limitations=["Public information only."],
            human_review_statement=(
                "This report requires human review."
            ),
        )


def test_insufficient_report_rejects_preferred_candidate() -> None:
    """Insufficient evidence cannot support a preferred candidate."""

    with pytest.raises(
        ValidationError,
        match="cannot identify a preferred candidate",
    ):
        ReportDraft(
            workflow_id=uuid4(),
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=(
                ReportType.INSUFFICIENT_EVIDENCE_REPORT
            ),
            recommendation_outcome=(
                RecommendationOutcome.INSUFFICIENT_EVIDENCE
            ),
            preferred_candidate="Company A",
            title="Insufficient Evidence Report",
            markdown_content="# Insufficient Evidence Report",
            risks=["A recommendation could be misleading."],
            limitations=["Required evidence is missing."],
            human_review_statement=(
                "This report requires human review."
            ),
        )


def test_insufficient_outcome_requires_matching_report_type() -> None:
    """Insufficient outcome requires an insufficient-evidence report."""

    with pytest.raises(
        ValidationError,
        match=(
            "requires an insufficient-evidence report"
        ),
    ):
        ReportDraft(
            workflow_id=uuid4(),
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=ReportType.RESEARCH_REPORT,
            recommendation_outcome=(
                RecommendationOutcome.INSUFFICIENT_EVIDENCE
            ),
            title="Investment Research Report",
            markdown_content="# Investment Research Report",
            risks=["A recommendation could be misleading."],
            limitations=["Required evidence is missing."],
            human_review_statement=(
                "This report requires human review."
            ),
        )


def test_report_rejects_duplicate_references() -> None:
    """Report record references should be unique."""

    source_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="Report reference identifiers must be unique",
    ):
        ReportDraft(
            workflow_id=uuid4(),
            validation_id=uuid4(),
            recommendation_id=uuid4(),
            report_type=ReportType.RESEARCH_REPORT,
            recommendation_outcome=(
                RecommendationOutcome.RESEARCH_SHORTLIST
            ),
            title="Investment Research Report",
            markdown_content="# Investment Research Report",
            risks=["Market risk."],
            limitations=["Public information only."],
            human_review_statement=(
                "This report requires human review."
            ),
            source_ids=[source_id, source_id],
        )


def test_created_markdown_artifact_accepts_valid_data() -> None:
    """A created Markdown artifact should preserve its path."""

    workflow_id = uuid4()
    report_draft_id = uuid4()

    artifact = create_markdown_artifact(
        workflow_id,
        report_draft_id,
    )

    assert artifact.status == ArtifactStatus.CREATED
    assert artifact.relative_path is not None
    assert artifact.file_name.endswith(".md")


@pytest.mark.parametrize(
    "relative_path",
    [
        "/tmp/report.md",
        "../report.md",
        "outputs/../../report.md",
    ],
)
def test_artifact_rejects_unsafe_path(
    relative_path: str,
) -> None:
    """Artifact paths must remain within the output directory."""

    with pytest.raises(ValidationError):
        ReportArtifact(
            workflow_id=uuid4(),
            report_draft_id=uuid4(),
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.CREATED,
            file_name="report.md",
            relative_path=relative_path,
            created_at=datetime.now(timezone.utc),
        )


def test_created_artifact_requires_path() -> None:
    """A created artifact requires an output path."""

    with pytest.raises(
        ValidationError,
        match="requires a relative path",
    ):
        ReportArtifact(
            workflow_id=uuid4(),
            report_draft_id=uuid4(),
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.CREATED,
            file_name="report.md",
            created_at=datetime.now(timezone.utc),
        )


def test_created_artifact_requires_timestamp() -> None:
    """A created artifact requires a creation timestamp."""

    with pytest.raises(
        ValidationError,
        match="requires a creation timestamp",
    ):
        ReportArtifact(
            workflow_id=uuid4(),
            report_draft_id=uuid4(),
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.CREATED,
            file_name="report.md",
            relative_path="outputs/report.md",
        )


def test_failed_artifact_requires_error() -> None:
    """A failed artifact must explain the failure."""

    with pytest.raises(
        ValidationError,
        match="requires an error message",
    ):
        ReportArtifact(
            workflow_id=uuid4(),
            report_draft_id=uuid4(),
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.FAILED,
            file_name="report.md",
        )


def test_markdown_artifact_requires_md_extension() -> None:
    """Markdown report artifacts require an md extension."""

    with pytest.raises(
        ValidationError,
        match="must use the .md extension",
    ):
        ReportArtifact(
            workflow_id=uuid4(),
            report_draft_id=uuid4(),
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.PENDING,
            file_name="report.txt",
        )


def test_artifact_file_name_must_match_path() -> None:
    """Artifact file name must match its output path."""

    with pytest.raises(
        ValidationError,
        match="file name must match",
    ):
        ReportArtifact(
            workflow_id=uuid4(),
            report_draft_id=uuid4(),
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.CREATED,
            file_name="report.md",
            relative_path="outputs/different.md",
            created_at=datetime.now(timezone.utc),
        )


def test_created_workflow_artifact_requires_both_outputs() -> None:
    """Completed artifact bundle requires Markdown and JSON outputs."""

    workflow_id = uuid4()
    report_draft_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="requires both Markdown and JSON output files",
    ):
        WorkflowArtifact(
            workflow_id=workflow_id,
            report_draft_id=report_draft_id,
            recommendation_id=uuid4(),
            validation_id=uuid4(),
            status=ArtifactStatus.CREATED,
            artifacts=[
                create_markdown_artifact(
                    workflow_id,
                    report_draft_id,
                )
            ],
        )


def test_created_workflow_artifact_accepts_both_outputs() -> None:
    """Completed bundle should contain Markdown and JSON outputs."""

    workflow_id = uuid4()
    report_draft_id = uuid4()

    workflow_artifact = WorkflowArtifact(
        workflow_id=workflow_id,
        report_draft_id=report_draft_id,
        recommendation_id=uuid4(),
        validation_id=uuid4(),
        status=ArtifactStatus.CREATED,
        artifacts=[
            create_markdown_artifact(
                workflow_id,
                report_draft_id,
            ),
            create_json_artifact(
                workflow_id,
                report_draft_id,
            ),
        ],
    )

    assert workflow_artifact.status == ArtifactStatus.CREATED
    assert len(workflow_artifact.artifacts) == 2


def test_workflow_artifact_rejects_mismatched_workflow() -> None:
    """Nested report artifacts must match the workflow."""

    workflow_id = uuid4()
    report_draft_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="must use the same workflow_id",
    ):
        WorkflowArtifact(
            workflow_id=workflow_id,
            report_draft_id=report_draft_id,
            recommendation_id=uuid4(),
            validation_id=uuid4(),
            status=ArtifactStatus.CREATED,
            artifacts=[
                create_markdown_artifact(
                    uuid4(),
                    report_draft_id,
                ),
                create_json_artifact(
                    workflow_id,
                    report_draft_id,
                ),
            ],
        )


def test_report_draft_serialization_round_trip() -> None:
    """A report draft should serialize and reconstruct."""

    report = create_report_draft(uuid4())

    serialized = report.model_dump_json()
    reconstructed = ReportDraft.model_validate_json(serialized)

    assert reconstructed == report


def test_workflow_artifact_serialization_round_trip() -> None:
    """A workflow artifact should serialize and reconstruct."""

    workflow_id = uuid4()
    report_draft_id = uuid4()

    workflow_artifact = WorkflowArtifact(
        workflow_id=workflow_id,
        report_draft_id=report_draft_id,
        recommendation_id=uuid4(),
        validation_id=uuid4(),
        status=ArtifactStatus.CREATED,
        artifacts=[
            create_markdown_artifact(
                workflow_id,
                report_draft_id,
            ),
            create_json_artifact(
                workflow_id,
                report_draft_id,
            ),
        ],
    )

    serialized = workflow_artifact.model_dump_json()
    reconstructed = WorkflowArtifact.model_validate_json(
        serialized
    )

    assert reconstructed == workflow_artifact