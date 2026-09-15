"""Offline smoke test for collision-safe Markdown report writing."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fin_automation.models.common import RecommendationOutcome, ReportType
from fin_automation.models.reports import ReportDraft
from fin_automation.tools.report_writer import ReportWriterTool


def create_report_draft() -> ReportDraft:
    """Create a minimal valid ReportDraft for the smoke test."""

    return ReportDraft(
        workflow_id=uuid4(),
        validation_id=uuid4(),
        recommendation_id=uuid4(),
        report_type=ReportType.RESEARCH_REPORT,
        recommendation_outcome=(
            RecommendationOutcome.QUALIFIED_RECOMMENDATION
        ),
        preferred_candidate="Smoke Test Candidate",
        title="Smoke Test Report",
        markdown_content=(
            "# Smoke Test Report\n\n"
            "## Research Question\n\nSmoke test question.\n\n"
            "## Investor Profile\n\nSmoke test profile.\n\n"
            "## Research Scope\n\nSmoke test scope.\n\n"
            "## Executive Summary\n\nSmoke test summary.\n\n"
            "## Research Methodology\n\nSmoke test method.\n\n"
            "## Candidate Analyses\n\nSmoke test analysis.\n\n"
            "## Candidate Comparison\n\nSmoke test comparison.\n\n"
            "## Recommendation Outcome\n\nSmoke test outcome.\n\n"
            "## Material Risks\n\nSmoke test risk.\n\n"
            "## Missing Information and Unresolved Conflicts\n\n"
            "None identified for this smoke test.\n\n"
            "## Limitations\n\nSmoke test limitation.\n\n"
            "## Sources\n\nSmoke test source.\n\n"
            "## Human Review\n\nHuman review is required.\n"
        ),
        risks=["Smoke-test risk"],
        limitations=["Smoke-test limitation"],
        human_review_statement=(
            "This report requires human review before use."
        ),
    )


def main() -> None:
    """Write three reports and verify collision-safe filenames."""

    original_directory = Path.cwd()

    with TemporaryDirectory() as temporary_directory:
        os.chdir(temporary_directory)
        try:
            writer = ReportWriterTool()
            report_draft = create_report_draft()
            report_content = report_draft.markdown_content
            expected_names = [
                "output/report1.md",
                "output/report2.md",
                "output/report3.md",
            ]

            written_paths = [
                writer.forward(report_draft).relative_path
                for _ in expected_names
            ]

            if written_paths != expected_names:
                raise AssertionError(
                    "Unexpected report filenames: "
                    f"{written_paths}"
                )

            for written_path in written_paths:
                path = Path(written_path)
                if not path.is_file():
                    raise AssertionError(
                        f"Expected report file was not created: {path}"
                    )
                if path.read_text(encoding="utf-8") != report_content:
                    raise AssertionError(
                        f"Report contents were not preserved: {path}"
                    )

            try:
                empty_draft = report_draft.model_copy(
                    update={"markdown_content": "   "}
                )
                writer.forward(empty_draft)
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "Empty report content should raise ValueError."
                )
        finally:
            os.chdir(original_directory)

    print("Report writer smoke test completed successfully.")
    print("Verified: report1.md, report2.md, report3.md")
    print("Verified: report contents are preserved.")
    print("Verified: empty report content is rejected.")


if __name__ == "__main__":
    main()
