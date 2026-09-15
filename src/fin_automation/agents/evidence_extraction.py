"""Evidence Extraction Agent implementation using smolagents."""

from datetime import date
from uuid import UUID

from smolagents import Model, ToolCallingAgent

from fin_automation.models.common import ParsingStatus
from fin_automation.models.research import EvidenceRequirement
from fin_automation.models.sources import (
    ExtractedEvidence,
    SelectedSource,
    SourceRecord,
)
from fin_automation.prompts.evidence_extraction import (
    EVIDENCE_EXTRACTION_SYSTEM_PROMPT,
    build_evidence_extraction_messages,
)
from fin_automation.tools.evidence_submission import (
    SubmitExtractedEvidenceTool,
)


class EvidenceExtractionAgent(ToolCallingAgent):
    """Extract factual evidence from selected Tavily source content."""

    def __init__(self, model_to_use: Model) -> None:
        """Initialize the Evidence Extraction Agent."""

        self._submission_tool = SubmitExtractedEvidenceTool()

        super().__init__(
            tools=[self._submission_tool],
            model=model_to_use,
            instructions=EVIDENCE_EXTRACTION_SYSTEM_PROMPT,
            max_steps=4,
            name="evidence_extraction_agent",
            description=(
                "Extracts factual evidence from selected public source "
                "content and submits validated evidence records."
            ),
        )

    def extract_evidence(
        self,
        selected_source: SelectedSource,
        evidence_requirements: list[EvidenceRequirement],
        workflow_id: UUID,
    ) -> tuple[SourceRecord, list[ExtractedEvidence], list[str]]:
        """Build a SourceRecord and extract evidence from one source."""

        source_record = self._build_source_record(
            selected_source=selected_source,
            workflow_id=workflow_id,
        )

        approved_requirement_ids = {
            requirement.requirement_id
            for requirement in evidence_requirements
        }

        source_requirement_ids = set(
            selected_source.evidence_requirement_ids
        )

        if not source_requirement_ids:
            raise ValueError(
                "The selected source does not reference an evidence requirement."
            )

        if not source_requirement_ids.issubset(approved_requirement_ids):
            raise ValueError(
                "The selected source references an evidence requirement "
                "outside the supplied extraction scope."
            )

        relevant_requirements = [
            requirement
            for requirement in evidence_requirements
            if requirement.requirement_id in source_requirement_ids
        ]

        self._submission_tool.begin_run(
            source_record=source_record,
            evidence_requirements=relevant_requirements,
        )

        messages = build_evidence_extraction_messages(
            source_record=source_record,
            raw_content=selected_source.raw_content or "",
            evidence_requirements=relevant_requirements,
        )

        self.run(messages[1]["content"], reset=True)

        return (
            source_record,
            self._submission_tool.accepted_evidence,
            self._submission_tool.evidence_gaps,
        )

    @staticmethod
    def _build_source_record(
        selected_source: SelectedSource,
        workflow_id: UUID,
    ) -> SourceRecord:
        """Construct a SourceRecord directly from a SelectedSource."""

        if not selected_source.selected:
            raise ValueError(
                "Evidence extraction requires a selected source."
            )

        raw_content = (selected_source.raw_content or "").strip()

        if not raw_content:
            raise ValueError(
                "Evidence extraction requires selected source content."
            )

        normalized_summary = " ".join(raw_content.split())[:500]
        limitations: list[str] = [
            "Source content was supplied as cleaned Tavily raw content, "
            "not original webpage HTML."
        ]

        if len(raw_content) >= 12_000:
            limitations.append(
                "Source content may be truncated at the configured "
                "12,000-character limit."
            )

        candidate_names = (
            [selected_source.candidate_name]
            if selected_source.candidate_name
            else []
        )

        return SourceRecord(
            workflow_id=workflow_id,
            retrieval_id=None,
            search_result_id=selected_source.search_result_id,
            title=selected_source.title,
            url=selected_source.url,
            publisher=selected_source.domain,
            author=None,
            publication_date=None,
            retrieval_date=date.today(),
            source_category=selected_source.expected_source_category,
            parsing_status=ParsingStatus.SUCCESS,
            candidate_names=candidate_names,
            evidence_requirement_ids=(
                selected_source.evidence_requirement_ids
            ),
            content_summary=normalized_summary,
            limitations=limitations,
        )
