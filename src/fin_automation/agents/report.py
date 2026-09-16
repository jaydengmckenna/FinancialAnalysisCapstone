"""Report Writing Agent implementation using smolagents."""

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
from fin_automation.models.reports import ReportArtifact, ReportDraft
from fin_automation.models.sources import (
    ExtractedEvidence,
    SourceRecord,
)
from fin_automation.models.validation import ValidationResult
from fin_automation.prompts.report import (
    REPORT_WRITING_SYSTEM_PROMPT,
    build_report_writing_messages,
)
from fin_automation.tools.report_writer import ReportWriterTool


class ReportAgent(ToolCallingAgent):
    """Generate and write a validated report from approved workflow data.

    The agent owns its own `ReportWriterTool` the same way
    `FinancialAnalysisAgent` owns `FinancialCalculationTool`: callers
    never touch the tool directly, they just call `generate_report()`
    with the approved workflow records, and the agent handles loading
    the tool's approved context and letting the model call it.
    """

    def __init__(
        self,
        model_to_use: Model,
        report_writer_tool: ReportWriterTool | None = None,
    ) -> None:
        """Initialize the Report Writing Agent.

        Args:
            model_to_use: A smolagents-compatible model instance.
            report_writer_tool: Optional writer tool override, mainly
                for tests that need a temporary output directory.
                Defaults to a normally configured `ReportWriterTool`.
        """

        self._report_writer_tool = (
            report_writer_tool or ReportWriterTool()
        )

        super().__init__(
            tools=[self._report_writer_tool],
            model=model_to_use,
            instructions=REPORT_WRITING_SYSTEM_PROMPT,
            max_steps=4,
            name="report_writing_agent",
            description=(
                "Transforms approved workflow records into a "
                "human-readable financial research report and writes "
                "it by calling the report_writer tool."
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
    ) -> tuple[ReportDraft, ReportArtifact]:
        """Generate, validate, and write one ReportDraft.

        Loads the writer tool with the approved workflow context, then
        runs the agent and lets it call that tool as its own action.
        The tool performs all JSON validation, identity checking
        against the approved records, structural/safety checks, and
        the actual file write; this method only reads back what the
        tool produced.

        Returns:
            The validated ReportDraft and the ReportArtifact describing
            the file that was written.

        Raises:
            ValueError: If the agent's run completes without
                successfully calling the report_writer tool.
        """

        self._report_writer_tool.begin_run(
            workflow_id=research_request.workflow_id,
            validation_result=validation_result,
            recommendation_result=recommendation_result,
            source_records=source_records,
            evidence_records=evidence_records,
            calculations=calculations,
            candidate_analyses=candidate_analyses,
        )

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

        self.run(
            messages[1]["content"],
            reset=True,
        )

        report_draft = self._report_writer_tool.last_draft
        report_artifact = self._report_writer_tool.last_artifact

        if report_draft is None or report_artifact is None:
            raise ValueError(
                "The agent did not successfully call the "
                "report_writer tool to submit and write the report."
            )

        return report_draft, report_artifact
