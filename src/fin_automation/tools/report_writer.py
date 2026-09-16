
from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from uuid import UUID

from pydantic import ValidationError
from smolagents import Tool
from fin_automation.config import get_settings
from fin_automation.models.common import ArtifactStatus, ArtifactType
from fin_automation.models.financial import (
    CalculatedMetric,
    CandidateAnalysis,
    RecommendationResult,
)
from fin_automation.models.reports import (
    ReportArtifact,
    ReportDraft,
)
from fin_automation.models.sources import ExtractedEvidence, SourceRecord
from fin_automation.models.validation import ValidationResult


class ReportWriterTool(Tool):
    """Tool for the Report Writing Agent to submit and write its report.

    The agent calls this tool directly as its own action, so `forward()`
    receives a raw JSON payload rather than an already-validated
    `ReportDraft` object. The tool is responsible for validating that
    payload, checking it against the approved workflow records loaded
    via `begin_run()`, applying the structural/safety checks, and
    writing the Markdown file. Nothing else in the workflow calls this
    tool's write path; the orchestrator only reads `last_artifact`
    afterward.
    """

    name = "report_writer"

    description = """
    Validate and write the final ReportDraft as a Markdown document.

    Call this tool exactly once, after building the complete report
    payload from the approved workflow records supplied in the task.

    Use only the report data you were given. Do not add any new
    information or make assumptions beyond the provided data.

    Do not generate report_draft_id or created_at. The application
    generates those fields.

    The payload must satisfy the ReportDraft schema. The tool returns a
    short confirmation once the report has been validated and written.
    """.strip()

    inputs = {
        "payload": {
            "type": "object",
            "description": (
                "The ReportDraft data to write, containing workflow_id, "
                "validation_id, recommendation_id, report_type, "
                "recommendation_outcome, preferred_candidate, title, "
                "markdown_content, risks, limitations, "
                "human_review_statement, and the approved "
                "candidate_analysis_ids, source_ids, evidence_ids, and "
                "calculation_ids."
            ),
        },
    }
    output_type = "string"

    def __init__(self, output_directory: Path | None = None) -> None:
        """Initialize the tool with the approved output directory.

        Args:
            output_directory: Directory to write reports into. Defaults
                to the configured, project-root-anchored `outputs`
                directory (`Settings.output_directory`) rather than a
                path relative to whatever the current working
                directory happens to be.
        """

        super().__init__()

        self._output_directory = (
            output_directory
            if output_directory is not None
            else get_settings().output_directory
        )

        self._workflow_id: UUID | None = None
        self._validation_result: ValidationResult | None = None
        self._recommendation_result: RecommendationResult | None = None
        self._known_ids: dict[str, set[UUID]] = {}
        self._approved_ids: dict[str, set[UUID]] = {}
        self._last_artifact: ReportArtifact | None = None
        self._last_draft: ReportDraft | None = None

    @property
    def last_artifact(self) -> ReportArtifact | None:
        """Return the most recently written ReportArtifact, if any."""

        return self._last_artifact

    @property
    def last_draft(self) -> ReportDraft | None:
        """Return the most recently validated ReportDraft, if any."""

        return self._last_draft

    def reset(self) -> None:
        """Clear the previously written artifact and draft."""

        self._last_artifact = None
        self._last_draft = None

    def begin_run(
        self,
        *,
        workflow_id: UUID,
        validation_result: ValidationResult,
        recommendation_result: RecommendationResult,
        source_records: list[SourceRecord],
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
        candidate_analyses: list[CandidateAnalysis],
    ) -> None:
        """Load the approved workflow context the agent's draft must match.

        The orchestrator calls this once, before handing the tool to
        the Report Writing Agent, so `forward()` can validate the
        agent's submitted draft against the same approved records that
        `ReportAgent._validate_report_identity` used to check
        afterward in Python.

        Args:
            workflow_id: Workflow the report draft must belong to.
            validation_result: The approved ValidationResult the draft
                must reference and stay within.
            recommendation_result: The recommendation the draft must
                reference and preserve.
            source_records: All source records produced this workflow.
            evidence_records: All evidence records produced this
                workflow.
            calculations: All calculations produced this workflow.
            candidate_analyses: All candidate analyses produced this
                workflow.
        """

        self._workflow_id = workflow_id
        self._validation_result = validation_result
        self._recommendation_result = recommendation_result

        self._known_ids = {
            "source_ids": {
                record.source_id for record in source_records
            },
            "evidence_ids": {
                record.evidence_id for record in evidence_records
            },
            "calculation_ids": {
                calculation.calculation_id
                for calculation in calculations
            },
            "candidate_analysis_ids": {
                analysis.analysis_id
                for analysis in candidate_analyses
            },
        }
        self._approved_ids = {
            "source_ids": set(validation_result.approved_source_ids),
            "evidence_ids": set(
                validation_result.approved_evidence_ids
            ),
            "calculation_ids": set(
                validation_result.approved_calculation_ids
            ),
            "candidate_analysis_ids": set(
                validation_result.approved_candidate_analysis_ids
            ),
        }
        self._last_artifact = None
        self._last_draft = None

    @staticmethod
    def _prepare_report_payload(payload: object) -> object:
        """Remove identifiers and timestamps the application generates.

        Args:
            payload: Report draft data supplied by the agent.

        Returns:
            The payload with application-owned fields removed so
            Pydantic generates them deterministically.
        """

        if not isinstance(payload, Mapping):
            return payload

        normalized_payload = dict(payload)
        normalized_payload.pop("report_draft_id", None)
        normalized_payload.pop("created_at", None)

        return normalized_payload

    def _validate_identity(self, report_draft: ReportDraft) -> None:
        """Check the submitted draft against the preloaded workflow context.

        Raises:
            RuntimeError: If `begin_run()` was never called.
            ValueError: If the draft does not correspond to the
                approved workflow, validation result, or recommendation.
        """

        if (
            self._workflow_id is None
            or self._validation_result is None
            or self._recommendation_result is None
        ):
            raise RuntimeError(
                "begin_run() must be called before the report writer "
                "tool can be used."
            )

        if report_draft.workflow_id != self._workflow_id:
            raise ValueError(
                "The report draft workflow_id does not match the "
                "approved workflow."
            )

        if (
            report_draft.validation_id
            != self._validation_result.validation_id
        ):
            raise ValueError(
                "The report draft does not reference the approved "
                "validation result."
            )

        if (
            report_draft.recommendation_id
            != self._recommendation_result.recommendation_id
        ):
            raise ValueError(
                "The report draft does not reference the approved "
                "recommendation."
            )

        for field_name, identifiers in (
            ("source_ids", report_draft.source_ids),
            ("evidence_ids", report_draft.evidence_ids),
            ("calculation_ids", report_draft.calculation_ids),
            (
                "candidate_analysis_ids",
                report_draft.candidate_analysis_ids,
            ),
        ):
            unknown_ids = (
                set(identifiers) - self._known_ids[field_name]
            )
            unapproved_ids = (
                set(identifiers) - self._approved_ids[field_name]
            )
            if unknown_ids:
                raise ValueError(
                    f"The report draft contains unknown {field_name}."
                )
            if unapproved_ids:
                raise ValueError(
                    "The report draft contains unapproved "
                    f"{field_name}."
                )

        if (
            report_draft.preferred_candidate
            != self._recommendation_result.preferred_candidate
        ):
            raise ValueError(
                "The report draft preferred candidate does not match "
                "the approved recommendation."
            )

    def forward(self, payload: dict[str, object]) -> str:
        """Validate the agent's report draft and write it to Markdown.

        Args:
            payload: Report draft data created by the agent.

        Returns:
            Confirmation that the report was validated and written.

        Raises:
            ValueError: If the payload violates the ReportDraft
                contract, does not match the approved workflow
                records, or fails the structural/safety checks.
        """

        if (
            self._workflow_id is None
            or self._validation_result is None
            or self._recommendation_result is None
        ):
            raise RuntimeError(
                "begin_run() must be called before the report writer "
                "tool can be used."
            )

        prepared_payload = self._prepare_report_payload(payload)

        try:
            report_draft = ReportDraft.model_validate(prepared_payload)
        except ValidationError as error:
            raise ValueError(
                "The submitted report draft does not satisfy the "
                f"ReportDraft contract:\n{error}"
            ) from error

        self._validate_identity(report_draft)
        self._report_structure_validation(report_draft)

        output_directory = self._output_directory
        output_directory.mkdir(parents=True, exist_ok=True)
        file_path = self._next_available_path(output_directory)

        # Write the report to the Markdown file
        markdown_content = report_draft.markdown_content
        with file_path.open("w", encoding="utf-8") as report_file:
            report_file.write(markdown_content)

        checksum = hashlib.sha256(
            markdown_content.encode("utf-8")
        ).hexdigest()

        artifact = ReportArtifact(
            workflow_id=report_draft.workflow_id,
            report_draft_id=report_draft.report_draft_id,
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.CREATED,
            file_name=file_path.name,
            relative_path=f"{output_directory.name}/{file_path.name}",
            checksum_sha256=checksum,
            created_at=datetime.now(timezone.utc),
        )
        self._last_artifact = artifact
        self._last_draft = report_draft

        return (
            "Report validated and written. "
            f"Status: {artifact.status.value}. "
            f"File: {artifact.relative_path}."
        )

    @staticmethod
    def _report_structure_validation(report: ReportDraft) -> None:
        """Validate required report headings and safety boundaries."""

        markdown_content = report.markdown_content.strip()
        if not markdown_content:
            raise ValueError("The report content is empty.")

        required_headings = {
            "research question",
            "investor profile",
            "research scope",
            "executive summary",
            "research methodology",
            "candidate analyses",
            "candidate comparison",
            "recommendation outcome",
            "material risks",
            "missing information and unresolved conflicts",
            "limitations",
            "sources",
            "human review",
        }
        headings = {
            match.group(1).strip().casefold()
            for match in re.finditer(
                r"^#{1,6}\s+(.+?)\s*#*\s*$",
                markdown_content,
                flags=re.MULTILINE,
            )
        }
        missing_headings = required_headings - headings
        if missing_headings:
            raise ValueError(
                "The report is missing required sections: "
                + ", ".join(sorted(missing_headings))
            )

        unsafe_phrases = (
            "guaranteed return",
            "guaranteed profit",
            "risk-free",
            "must buy",
            "must sell",
            "execute a trade",
            "place an order",
        )
        normalized_content = markdown_content.casefold()
        unsafe_matches = [
            phrase
            for phrase in unsafe_phrases
            if phrase in normalized_content
        ]
        if unsafe_matches:
            raise ValueError(
                "The report contains prohibited language: "
                + ", ".join(unsafe_matches)
            )

        if "human review" not in report.human_review_statement.casefold():
            raise ValueError(
                "The report must include a human-review statement."
            )

        insufficient_outcome = (
            report.recommendation_outcome.value
            == "insufficient_evidence"
        )
        if insufficient_outcome and report.preferred_candidate is not None:
            raise ValueError(
                "An insufficient-evidence report cannot identify a "
                "preferred candidate."
            )

    @staticmethod
    def _next_available_path(output_directory: Path) -> Path:
        """Return report.md or the next available numbered filename."""

        counter = 1
        while True:
            report_path = output_directory / f"report{counter}.md"
            if not report_path.exists():
                return report_path
            counter += 1
