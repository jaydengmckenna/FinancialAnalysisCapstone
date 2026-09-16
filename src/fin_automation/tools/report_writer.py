
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from smolagents import Tool
from fin_automation.config import get_settings
from fin_automation.models.common import ArtifactStatus, ArtifactType
from fin_automation.models.reports import (
    ReportArtifact,
    ReportDraft,
)


class ReportWriterTool(Tool):
    """Tool for writing reports."""

    name = "report_writer"
    
    description = """
    Write a validated ReportDraft Markdown document to the output directory.

    Use only the report data provided in the input JSON. 
    Do not add any new information or make assumptions beyond the 
    provided data.

    The tool returns a validated ReportArtifact.
    """.strip()

    inputs = {
        "report_content": {
            "type": "object",
            "description": "Validated ReportDraft to write as Markdown.",
        },
    }
    output_type = "object"

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

    def forward(self, report_content: ReportDraft) -> ReportArtifact:
        """Write the report to Markdown file."""

        self._report_structure_validation(report_content)

        output_directory = self._output_directory
        output_directory.mkdir(parents=True, exist_ok=True)
        file_path = self._next_available_path(output_directory)

        # Write the report to the Markdown file
        markdown_content = report_content.markdown_content
        with file_path.open("w", encoding="utf-8") as report_file:
            report_file.write(markdown_content)

        checksum = hashlib.sha256(
            markdown_content.encode("utf-8")
        ).hexdigest()

        return ReportArtifact(
            workflow_id=report_content.workflow_id,
            report_draft_id=report_content.report_draft_id,
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            status=ArtifactStatus.CREATED,
            file_name=file_path.name,
            relative_path=f"{output_directory.name}/{file_path.name}",
            checksum_sha256=checksum,
            created_at=datetime.now(timezone.utc),
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
