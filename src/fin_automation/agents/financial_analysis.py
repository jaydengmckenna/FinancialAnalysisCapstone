"""Minimal Financial Analysis Agent for Phase 6."""

from datetime import date
import re
from uuid import UUID, uuid4

from pydantic import AnyHttpUrl
from smolagents import Model, ToolCallingAgent

from fin_automation.models.common import ParsingStatus, SourceCategory
from fin_automation.models.financial import CalculatedMetric
from fin_automation.models.research import EvidenceRequirement
from fin_automation.models.sources import ExtractedEvidence, SourceRecord
from fin_automation.prompts.financial_analysis import (
    FINANCIAL_ANALYSIS_SYSTEM_PROMPT,
    build_financial_analysis_task,
)
from fin_automation.tools.financial_calculation import (
    FinancialCalculationTool,
)
from fin_automation.tools.financial_data import (
    FinancialDataPoint,
    FinancialDataTool,
)


class FinancialAnalysisAgent(ToolCallingAgent):
    """Select calculations and interpret validated results."""

    # yfinance typically exposes about 4-5 annual periods; searching a
    # little beyond that is cheap and harmless, and stops us from
    # scanning indefinitely for a year that was never reported.
    _MAX_FISCAL_YEAR_LOOKBACK = 6

    def __init__(self, model_to_use: Model) -> None:
        """Initialize the Financial Analysis Agent."""

        self._calculation_tool = FinancialCalculationTool()
        self._fill_data = FinancialDataTool()

        super().__init__(
            tools=[self._calculation_tool],
            model=model_to_use,
            instructions=FINANCIAL_ANALYSIS_SYSTEM_PROMPT,
            max_steps=4,
            name="financial_analysis_agent",
            description=(
                "Selects bounded financial calculations, calls "
                "deterministic Python tooling, and interprets "
                "validated results."
            ),
        )

    def analyze(
        self,
        evidence: list[ExtractedEvidence],
        evidence_requirements: list[EvidenceRequirement],
        workflow_id: UUID,
    ) -> tuple[
        list[CalculatedMetric],
        str,
        list[ExtractedEvidence],
        list[SourceRecord],
    ]:
        """Analyze extracted evidence using deterministic calculations.

        Before asking the model to calculate anything, fills any
        evidence gaps that yfinance can answer directly (a named
        ticker's plain financial-statement figure), so the model has
        real numbers to work with even when web search alone did not
        find them.

        Returns:
            A tuple of (accepted calculations, the model's closing
            interpretation, any new evidence yfinance filled in, and
            the source records those new evidence records cite). The
            caller is responsible for merging the new evidence/source
            records into the workflow's own lists before validation.
        """

        new_evidence, new_sources = self._fill_missing_evidence(
            evidence=evidence,
            evidence_requirements=evidence_requirements,
            workflow_id=workflow_id,
        )
        combined_evidence = evidence + new_evidence

        if not combined_evidence:
            # Nothing from web research and nothing yfinance could fill.
            # begin_run() requires non-empty evidence, so stop here
            # rather than let that raise mid-call.
            return (
                [],
                "No evidence was available for financial analysis.",
                new_evidence,
                new_sources,
            )

        self._calculation_tool.begin_run(
            workflow_id=workflow_id,
            evidence=combined_evidence,
        )

        task = build_financial_analysis_task(combined_evidence)

        final_answer = str(
            self.run(
                task,
                reset=True,
            )
        )

        return (
            self._calculation_tool.accepted_calculations,
            final_answer,
            new_evidence,
            new_sources,
        )

    def _fill_missing_evidence(
        self,
        evidence: list[ExtractedEvidence],
        evidence_requirements: list[EvidenceRequirement],
        workflow_id: UUID,
    ) -> tuple[list[ExtractedEvidence], list[SourceRecord]]:
        """Fetch yfinance data for requirements nothing else covered.

        Only attempts requirements that (a) nothing in `evidence`
        already satisfies, (b) look like a recognized financial
        metric, and (c) carry a ticker. Anything yfinance can't answer
        is left as a gap for the rest of the workflow to handle, the
        same as before this existed.
        """

        gaps = [
            requirement
            for requirement in evidence_requirements
            if not self._is_covered(requirement, evidence)
        ]

        new_evidence: list[ExtractedEvidence] = []
        new_sources: list[SourceRecord] = []

        for requirement in gaps:
            if self._fill_data.resolve_metric_row(requirement.name) is None:
                continue
            if requirement.ticker is None:
                continue

            data_point = self._find_matching_fiscal_year(requirement)
            if data_point is None:
                continue

            source = SourceRecord(
                workflow_id=workflow_id,
                search_result_id=uuid4(),
                title=f"{data_point.company_name} — Yahoo Finance Financials",
                url=AnyHttpUrl(data_point.source_url),
                retrieval_date=date.today(),
                source_category=SourceCategory.SECONDARY,
                parsing_status=ParsingStatus.SUCCESS,
                candidate_names=(
                    [requirement.candidate_name]
                    if requirement.candidate_name
                    else []
                ),
                evidence_requirement_ids=[requirement.requirement_id],
                content_summary=(
                    f"{data_point.metric_name} from Yahoo Finance."
                ),
            )
            record = ExtractedEvidence(
                workflow_id=workflow_id,
                source_id=source.source_id,
                candidate_name=requirement.candidate_name,
                evidence_requirement_id=requirement.requirement_id,
                evidence_type="financial_metric",
                content=(
                    f"{data_point.company_name} reported "
                    f"{data_point.metric_name} of {data_point.value} "
                    f"{data_point.unit} {data_point.currency} for the "
                    f"fiscal period ended {data_point.fiscal_period_end}."
                ),
                reported_value=data_point.value,
                currency=data_point.currency,
                unit=data_point.unit,
                reporting_period=str(data_point.fiscal_period_end),
            )

            new_sources.append(source)
            new_evidence.append(record)

        return new_evidence, new_sources

    def _is_covered(
        self,
        requirement: EvidenceRequirement,
        evidence: list[ExtractedEvidence],
    ) -> bool:
        """Return whether any extracted evidence satisfies this requirement."""

        return any(
            record.evidence_requirement_id == requirement.requirement_id
            for record in evidence
        )

    @staticmethod
    def _extract_year(requirement: EvidenceRequirement) -> int | None:
        """Pull the 4-digit year mentioned in a requirement's text, if any."""

        match = re.search(
            r"20\d{2}",
            f"{requirement.name} {requirement.description}",
        )
        return int(match.group()) if match else None

    def _find_matching_fiscal_year(
        self,
        requirement: EvidenceRequirement,
    ) -> FinancialDataPoint | None:
        """Search recent fiscal years for the one a requirement asks for.

        Tries the most recently completed fiscal year first, then
        works backward, until it finds a fiscal year whose end date
        falls in the year the requirement's text mentions. If the
        requirement doesn't mention a specific year at all, the most
        recently completed fiscal year is used directly. Searching
        (rather than guessing a single offset) is what lets this find
        a requested year even when it is no longer the most recent one
        available.
        """

        if requirement.ticker is None:
            return None

        requested_year = self._extract_year(requirement)

        for period_offset in range(self._MAX_FISCAL_YEAR_LOOKBACK):
            data_point = self._fill_data.fetch_metric(
                ticker=requirement.ticker,
                metric_name=requirement.name,
                period_offset=period_offset,
            )
            if data_point is None:
                # No more fiscal-year history available from this
                # point on; further offsets would fail too.
                return None

            if requested_year is None:
                return data_point

            if data_point.fiscal_period_end.year == requested_year:
                return data_point

        return None
