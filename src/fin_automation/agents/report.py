"""Report Writing Agent implementation using smolagents."""

import json
from collections.abc import Mapping

from pydantic import BaseModel, ValidationError
from smolagents import Model, ToolCallingAgent

from fin_automation.models.financial import (
    CalculatedMetric,
    CandidateAnalysis,
    RecommendationResult,
)
from fin_automation.models.intake import (
    InvestorProfile,
    ResearchRequest,
    ResearchScope,
)
from fin_automation.models.research import ResearchPlan
from fin_automation.models.reports import ReportDraft
from fin_automation.models.sources import (
    ExtractedEvidence,
    SourceRecord,
)
from fin_automation.prompts.report import (
    REPORT_WRITING_SYSTEM_PROMPT,
    build_report_writing_messages,
)
from fin_automation.models.validation import ValidationResult


class ReportAgent(ToolCallingAgent):
    """Generate a validated report draft from approved workflow data."""

    def __init__(self, model_to_use: Model) -> None:
        """Initialize the Report Writing Agent."""

        super().__init__(
            tools=[],
            model=model_to_use,
            instructions=REPORT_WRITING_SYSTEM_PROMPT,
            max_steps=4,
            name="report_writing_agent",
            description=(
                "Transforms approved workflow records into a human-readable "
                "financial research report."
            ),
        )


    def generate_report(
        self,
        research_request: ResearchRequest,
        investor_profile: InvestorProfile,
        research_scope: ResearchScope,
        research_plan: ResearchPlan,
        source_records: list[SourceRecord],
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
        candidate_analyses: list[CandidateAnalysis],
        recommendation_result: RecommendationResult,
        validation_result: ValidationResult,
    ) -> ReportDraft:
        """Generate and validate one ReportDraft."""

        messages = build_report_writing_messages(
            research_request=research_request,
            investor_profile=investor_profile,
            research_scope=research_scope,
            research_plan=research_plan,
            source_records=source_records,
            evidence_records=evidence_records,
            calculations=calculations, 
            candidate_analyses=candidate_analyses,
            recommendation_result=recommendation_result,
            validation_result=validation_result,
        )

        raw_result = self.run(
            messages[1]["content"],
            reset=True,
        )

        report_draft = self._parse_report_draft(raw_result)
        self._validate_report_identity(
            report_draft=report_draft,
            research_request=research_request,
            recommendation_result=recommendation_result,
            validation_result=validation_result,
            source_records=source_records,
            evidence_records=evidence_records,
            calculations=calculations,
            candidate_analyses=candidate_analyses,
        )

        return report_draft

    @staticmethod
    def _parse_report_draft(raw_result: object) -> ReportDraft:
        """Convert the model response into a validated ReportDraft."""

        if isinstance(raw_result, ReportDraft):
            return raw_result

        if isinstance(raw_result, BaseModel):
            raw_result = raw_result.model_dump(mode="json")

        if isinstance(raw_result, Mapping):
            try:
                return ReportDraft.model_validate(dict(raw_result))
            except ValidationError as error:
                raise ValueError(
                    "The agent returned an invalid report draft."
                ) from error

        raw_text = str(raw_result).strip()
        if not raw_text:
            raise ValueError("The agent returned an empty report draft.")

        cleaned_text = ReportAgent._remove_markdown_code_fence(raw_text)
        try:
            parsed_json = json.loads(cleaned_text)
        except json.JSONDecodeError as error:
            raise ValueError(
                "The agent did not return valid JSON for ReportDraft."
            ) from error

        try:
            return ReportDraft.model_validate(parsed_json)
        except ValidationError as error:
            raise ValueError(
                "The agent returned JSON that does not satisfy the "
                "ReportDraft contract."
            ) from error

    @staticmethod
    def _remove_markdown_code_fence(text: str) -> str:
        """Remove one optional Markdown JSON code fence."""

        stripped_text = text.strip()
        if not stripped_text.startswith("```"):
            return stripped_text

        lines = stripped_text.splitlines()
        if len(lines) < 3:
            return stripped_text

        if lines[0].strip() not in {"```", "```json", "```JSON"}:
            return stripped_text

        if lines[-1].strip() != "```":
            return stripped_text

        return "\n".join(lines[1:-1]).strip()

    @staticmethod
    def _validate_report_identity(
        *,
        report_draft: ReportDraft,
        research_request: ResearchRequest,
        recommendation_result: RecommendationResult,
        validation_result: ValidationResult,
        source_records: list[SourceRecord],
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
        candidate_analyses: list[CandidateAnalysis],
    ) -> None:
        """Ensure the draft belongs to the approved workflow records."""

        if report_draft.workflow_id != research_request.workflow_id:
            raise ValueError(
                "The report draft workflow_id does not match the request."
            )

        if report_draft.validation_id != validation_result.validation_id:
            raise ValueError(
                "The report draft does not reference the validation result."
            )

        if report_draft.recommendation_id != recommendation_result.recommendation_id:
            raise ValueError(
                "The report draft does not reference the recommendation."
            )

        available_ids = {
            "source_ids": {record.source_id for record in source_records},
            "evidence_ids": {
                record.evidence_id for record in evidence_records
            },
            "calculation_ids": {
                record.calculation_id for record in calculations
            },
            "candidate_analysis_ids": {
                analysis.analysis_id for analysis in candidate_analyses
            },
        }
        approved_ids = {
            "source_ids": set(validation_result.approved_source_ids),
            "evidence_ids": set(validation_result.approved_evidence_ids),
            "calculation_ids": set(
                validation_result.approved_calculation_ids
            ),
            "candidate_analysis_ids": set(
                validation_result.approved_candidate_analysis_ids
            ),
        }

        for field_name, identifiers in (
            ("source_ids", report_draft.source_ids),
            ("evidence_ids", report_draft.evidence_ids),
            ("calculation_ids", report_draft.calculation_ids),
            ("candidate_analysis_ids", report_draft.candidate_analysis_ids),
        ):
            unknown_ids = set(identifiers) - available_ids[field_name]
            unapproved_ids = set(identifiers) - approved_ids[field_name]
            if unknown_ids:
                raise ValueError(
                    f"The report draft contains unknown {field_name}."
                )
            if unapproved_ids:
                raise ValueError(
                    f"The report draft contains unapproved {field_name}."
                )

        if (
            report_draft.preferred_candidate
            != recommendation_result.preferred_candidate
        ):
            raise ValueError(
                "The report draft preferred candidate does not match "
                "the approved recommendation."
            )

        