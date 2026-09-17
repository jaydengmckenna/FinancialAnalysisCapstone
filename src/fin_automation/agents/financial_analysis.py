"""Minimal Financial Analysis Agent for Phase 6."""

from datetime import date
import logging
import re
from uuid import UUID, uuid4

from pydantic import AnyHttpUrl
from smolagents import Model, ToolCallingAgent
import yfinance

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


logger = logging.getLogger(__name__)


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

        logger.info(
            "Financial Analysis Agent starting: %d evidence record(s) "
            "on hand, %d evidence requirement(s) to satisfy.",
            len(evidence),
            len(evidence_requirements),
        )

        new_evidence, new_sources = self._fill_missing_evidence(
            evidence=evidence,
            evidence_requirements=evidence_requirements,
            workflow_id=workflow_id,
        )
        combined_evidence = evidence + new_evidence

        for record in combined_evidence:
            logger.info(
                "Evidence on hand: %s %s = %s %s %s (%s).",
                record.candidate_name or "unknown candidate",
                record.evidence_type,
                record.reported_value,
                record.unit or "",
                record.currency or "",
                record.reporting_period or "period unknown",
            )

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

        for calculation in self._calculation_tool.accepted_calculations:
            logger.info(
                "Calculated %s for %s: %s %s.",
                calculation.metric_name,
                ", ".join(calculation.candidate_names),
                calculation.value,
                calculation.unit or "",
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

        if not gaps:
            logger.info(
                "Financial Analysis Agent: all evidence requirements "
                "already covered; yfinance not needed."
            )
            return [], []

        new_evidence: list[ExtractedEvidence] = []
        new_sources: list[SourceRecord] = []

        for requirement in gaps:
            if self._fill_data.resolve_metric_row(requirement.name) is None:
                logger.info(
                    "Evidence gap '%s' (%s) is not a recognized "
                    "financial metric; yfinance cannot help, leaving "
                    "as a gap.",
                    requirement.name,
                    requirement.candidate_name or "unknown candidate",
                )
                continue

            if requirement.candidate_name is None:
                logger.info(
                    "Evidence gap '%s' has no candidate name; yfinance "
                    "cannot look it up, leaving as a gap.",
                    requirement.name,
                )
                continue

            # Prefer the ticker the research plan already supplied.
            # Only fall back to a live search when it's missing, and
            # never write the result back onto `requirement` — that
            # object is shared with the rest of the workflow (it lives
            # inside research_plan.evidence_requirements), and this is
            # a lookup, not something that should silently rewrite the
            # plan.
            ticker = requirement.ticker
            if ticker is None:
                ticker = self._resolve_ticker(requirement.candidate_name)
            if ticker is None:
                logger.info(
                    "No ticker available for '%s' (%s); yfinance cannot "
                    "help, leaving as a gap.",
                    requirement.name,
                    requirement.candidate_name,
                )
                continue

            # A requirement can mention more than one year at once (a
            # combined "growth from FY2022 to FY2023" requirement, not
            # two separate ones), and existing evidence may already
            # cover some of those years correctly. Only fetch the
            # years still missing, so a single wrong/incomplete year
            # doesn't cause yfinance to re-fetch data already on hand.
            requested_years = self._extract_years(requirement)
            covered_years = self._covered_years(requirement, evidence)
            missing_years = [
                year for year in requested_years if year not in covered_years
            ] or [None]

            logger.info(
                "Financial Analysis Agent: falling back to yfinance for "
                "'%s' — candidate=%s, ticker=%s, year(s) needed=%s.",
                requirement.name,
                requirement.candidate_name,
                ticker,
                missing_years if requested_years else "most recent",
            )

            for target_year in missing_years:
                data_point = self._find_data_point_for_year(
                    requirement=requirement,
                    ticker=ticker,
                    target_year=target_year,
                )
                if data_point is None:
                    logger.info(
                        "yfinance found no matching data for ticker=%s, "
                        "year=%s ('%s').",
                        ticker,
                        target_year,
                        requirement.name,
                    )
                    continue

                logger.info(
                    "yfinance found %s = %s %s %s for %s (%s), fiscal "
                    "year ended %s.",
                    data_point.metric_name,
                    data_point.value,
                    data_point.unit,
                    data_point.currency,
                    data_point.ticker,
                    data_point.company_name,
                    data_point.fiscal_period_end,
                )

                source = SourceRecord(
                    workflow_id=workflow_id,
                    search_result_id=uuid4(),
                    title=(
                        f"{data_point.company_name} — "
                        "Yahoo Finance Financials"
                    ),
                    url=AnyHttpUrl(data_point.source_url),
                    retrieval_date=date.today(),
                    source_category=SourceCategory.SECONDARY,
                    parsing_status=ParsingStatus.SUCCESS,
                    candidate_names=[requirement.candidate_name],
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
                        f"{data_point.unit} {data_point.currency} for "
                        f"the fiscal period ended "
                        f"{data_point.fiscal_period_end}."
                    ),
                    reported_value=data_point.value,
                    currency=data_point.currency,
                    unit=data_point.unit,
                    # "FY{year}" matches the convention every other
                    # evidence record in this project already uses (see
                    # the "annual" branch of the validator's
                    # period-granularity check). The exact
                    # fiscal-period-end date is still preserved in
                    # `content` above for precision; this field only
                    # needs to say which fiscal year, consistently with
                    # how web-sourced evidence already labels the same
                    # thing, so the two can be compared without a false
                    # "incompatible granularity" rejection.
                    reporting_period=f"FY{data_point.fiscal_period_end.year}",
                )

                new_sources.append(source)
                new_evidence.append(record)

        if new_evidence:
            logger.info(
                "Financial Analysis Agent: yfinance filled %d of %d "
                "evidence gap(s).",
                len(new_evidence),
                len(gaps),
            )
        else:
            logger.info(
                "Financial Analysis Agent: %d evidence gap(s) found, "
                "yfinance did not fill any of them.",
                len(gaps),
            )

        return new_evidence, new_sources

    @staticmethod
    def _is_covered(
        requirement: EvidenceRequirement,
        evidence: list[ExtractedEvidence],
    ) -> bool:
        """Return whether extracted evidence satisfies this requirement.

        A matching requirement_id alone isn't enough:

        - A metric like revenue or gross profit growth needs a
          currency-denominated dollar value to calculate from.
          Evidence expressed only as a percentage or ratio (margin,
          growth rate, etc.) can't be used as that input even though
          it's tagged to the right requirement.
        - If the requirement asks about specific year(s) (e.g. "FY2022
          to FY2023"), evidence for a *different* year (a quarterly
          figure, or the wrong fiscal year) doesn't answer the
          question either, even though it may be a perfectly valid
          dollar amount for its own period.

        Both are checked via `_qualifying_records`/`_covered_years`
        rather than accepting the first matching-ID record found,
        since either kind of mismatch would otherwise silently block
        the yfinance fallback from supplying the actual right number.
        """

        qualifying = FinancialAnalysisAgent._qualifying_records(
            requirement, evidence
        )
        if not qualifying:
            return False

        requested_years = FinancialAnalysisAgent._extract_years(requirement)
        if not requested_years:
            return True

        covered_years = FinancialAnalysisAgent._covered_years(
            requirement, evidence
        )
        return all(year in covered_years for year in requested_years)

    @staticmethod
    def _qualifying_records(
        requirement: EvidenceRequirement,
        evidence: list[ExtractedEvidence],
    ) -> list[ExtractedEvidence]:
        """Evidence tagged to this requirement that is a usable dollar value."""

        return [
            record
            for record in evidence
            if record.evidence_requirement_id == requirement.requirement_id
            and record.currency is not None
            and not FinancialAnalysisAgent._is_percentage_unit(record.unit)
        ]

    @staticmethod
    def _covered_years(
        requirement: EvidenceRequirement,
        evidence: list[ExtractedEvidence],
    ) -> set[int]:
        """Years already backed by a qualifying evidence record."""

        return {
            year
            for record in FinancialAnalysisAgent._qualifying_records(
                requirement, evidence
            )
            for year in FinancialAnalysisAgent._years_in_text(
                record.reporting_period or ""
            )
        }

    @staticmethod
    def _is_percentage_unit(unit: str | None) -> bool:
        """Return whether a unit string describes a percentage or ratio."""

        if unit is None:
            return False

        normalized = unit.casefold()
        return "%" in normalized or "percent" in normalized

    @staticmethod
    def _years_in_text(text: str) -> list[int]:
        """Return every distinct 4-digit year mentioned in text, in order."""

        years: list[int] = []
        for match in re.findall(r"20\d{2}", text):
            year = int(match)
            if year not in years:
                years.append(year)
        return years

    @staticmethod
    def _extract_years(requirement: EvidenceRequirement) -> list[int]:
        """Pull every distinct year mentioned in a requirement's text."""

        return FinancialAnalysisAgent._years_in_text(
            f"{requirement.name} {requirement.description}"
        )

    def _find_data_point_for_year(
        self,
        requirement: EvidenceRequirement,
        ticker: str,
        target_year: int | None,
    ) -> FinancialDataPoint | None:
        """Search recent fiscal years for one specific year of data.

        Tries the most recently completed fiscal year first, then
        works backward, until it finds a fiscal year whose end date
        falls in `target_year`. If `target_year` is None, the most
        recently completed fiscal year is used directly. Searching
        (rather than guessing a single offset) is what lets this find
        a requested year even when it is no longer the most recent one
        available.
        """

        for period_offset in range(self._MAX_FISCAL_YEAR_LOOKBACK):
            data_point = self._fill_data.fetch_metric(
                ticker=ticker,
                metric_name=requirement.name,
                period_offset=period_offset,
            )
            if data_point is None:
                # No more fiscal-year history available from this
                # point on; further offsets would fail too.
                return None

            if target_year is None:
                return data_point

            if data_point.fiscal_period_end.year == target_year:
                return data_point

        return None

    @staticmethod
    def _resolve_ticker(company_name: str) -> str | None:
        """Look up a ticker symbol for a company name, as a fallback.

        Only used when the research plan didn't supply a ticker
        directly. yfinance is an unofficial wrapper around Yahoo's
        endpoints and can fail for reasons unrelated to whether a
        match exists (network errors, upstream changes, rate
        limiting), so any failure is treated the same as a genuine
        "no match found" rather than raised.
        """

        try:
            result = yfinance.Search(company_name, max_results=1)
        except Exception:
            logger.info(
                "Ticker search failed for '%s'; leaving as a gap.",
                company_name,
            )
            return None

        if not result.quotes:
            logger.info("No ticker found for '%s'.", company_name)
            return None

        ticker = result.quotes[0].get("symbol")
        logger.info(
            "Resolved ticker for '%s' via search: %s.",
            company_name,
            ticker,
        )
        return ticker
