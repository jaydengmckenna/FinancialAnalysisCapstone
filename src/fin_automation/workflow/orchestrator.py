"""Orchestration for the full planned research workflow."""

from decimal import Decimal
import logging
from typing import Any
from uuid import UUID, uuid4

from smolagents import Model, OpenAIServerModel

from fin_automation.agents.evidence_extraction import EvidenceExtractionAgent
from fin_automation.agents.evidence_validation import EvidenceValidationAgent
from fin_automation.agents.financial_analysis import FinancialAnalysisAgent
from fin_automation.agents.report import ReportAgent
from fin_automation.agents.research_planner import ResearchPlanner
from fin_automation.agents.source_selection import SourceSelectionAgent
from fin_automation.config import get_settings
from fin_automation.exceptions import WorkflowError
from fin_automation.models.common import (
    AnalysisStatus,
    CalculationOperation,
    ConfidenceLevel,
    DataAvailabilityStatus,
    RecommendationOutcome,
    SearchPurpose,
    WorkflowStage,
)
from fin_automation.models.financial import (
    CalculatedMetric,
    CandidateAnalysis,
    CategoryEvaluation,
    RecommendationResult,
)
from fin_automation.models.intake import IntakeResult
from fin_automation.models.research import (
    AdditionalResearchRequest,
    EvidenceRequirement,
    ResearchPlan,
)
from fin_automation.models.reports import ReportArtifact, ReportDraft
from fin_automation.models.sources import (
    ExtractedEvidence,
    SourceRecord,
    SourceSelection,
)
from fin_automation.models.validation import ValidationClaim, ValidationResult
from fin_automation.tools.tavily_search import TavilySearchTool


logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Coordinate the workflow while specialist agents own model work."""

    _MAX_MODEL_ATTEMPTS = 3

    def __init__(
        self,
        model_to_use: Model | None = None,
        research_planner: ResearchPlanner | None = None,
        source_selection_agent: SourceSelectionAgent | None = None,
        evidence_extraction_agent: EvidenceExtractionAgent | None = None,
        financial_analysis_agent: FinancialAnalysisAgent | None = None,
        evidence_validation_agent: EvidenceValidationAgent | None = None,
        report_agent: ReportAgent | None = None,
    ) -> None:
        """Initialize the workflow components."""

        settings = get_settings()

        if model_to_use is None:
            model_to_use = OpenAIServerModel(
                model_id=settings.model_id,
                api_key=settings.openai_api_key.get_secret_value(),
                api_base=str(settings.openai_base_url),
            )

        self.model = model_to_use
        self.research_planner = research_planner or ResearchPlanner(
            model_to_use=self.model,
        )

        if source_selection_agent is None:
            self.source_selection_agent = SourceSelectionAgent(
                model_to_use=self.model,
                tavily_search_tool=TavilySearchTool(
                    api_key=settings.tavily_api_key.get_secret_value(),
                ),
            )
        else:
            self.source_selection_agent = source_selection_agent

        self.evidence_extraction_agent = (
            evidence_extraction_agent
            or EvidenceExtractionAgent(model_to_use=self.model)
        )
        self.financial_analysis_agent = (
            financial_analysis_agent
            or FinancialAnalysisAgent(model_to_use=self.model)
        )
        self.evidence_validation_agent = (
            evidence_validation_agent or EvidenceValidationAgent()
        )
        self.report_agent = report_agent or ReportAgent(model_to_use=self.model)

        self.last_intake_result: IntakeResult | None = None
        self.last_research_plan: ResearchPlan | None = None
        self.last_source_selection: SourceSelection | None = None
        self.last_source_records: list[SourceRecord] = []
        self.last_evidence_records: list[ExtractedEvidence] = []
        self.last_calculations: list[CalculatedMetric] = []
        self.last_candidate_analyses: list[CandidateAnalysis] = []
        self.last_recommendation: RecommendationResult | None = None
        self.last_validation_result: ValidationResult | None = None
        self.last_report_draft: ReportDraft | None = None
        self.last_report_artifact: Any = None

    def _resolve_clarification(
        self,
        original_prompt: str,
        intake_result: IntakeResult,
        workflow_id: UUID,
        clarification_context: list[tuple[str, str]] | None = None,
    ) -> list[tuple[str, str]]:
        """Ask the user for clarification and preserve the original prompt."""

        print("Clarification required:")
        for question in intake_result.clarification_questions:
            print(f"- {question}")

        updated_context = list(clarification_context or [])
        for question in intake_result.clarification_questions:
            answer = input(f"{question}\nYour answer: ").strip()
            updated_context.append((question, answer))

        return updated_context

    def _run_with_retries(self, stage_name: str, action) -> Any:
        """Retry a fragile model-backed action a bounded number of times.

        Structured-output agents occasionally return malformed or
        internally inconsistent data (invalid identifiers, an altered
        scope, a mismatched workflow id). The parsing and validation
        layers raise a `ValueError` for each of those cases. Retrying
        the same call recovers most of them, since each attempt is an
        independent model call; exhausting the bounded attempt budget
        raises a structured `WorkflowError` instead of letting a raw
        traceback reach the caller, matching the "recoverable failures
        use bounded correction paths, unrecoverable failures produce
        structured errors" requirement.

        Args:
            stage_name: Human-readable stage name used in log output
                and the eventual `WorkflowError` message.
            action: Zero-argument callable that performs one attempt.

        Returns:
            The successful result of `action`.

        Raises:
            WorkflowError: If every attempt raises a `ValueError`.
        """

        last_error: ValueError | None = None
        for attempt in range(1, self._MAX_MODEL_ATTEMPTS + 1):
            try:
                return action()
            except ValueError as error:
                last_error = error
                logger.warning(
                    "%s attempt %d of %d failed: %s",
                    stage_name,
                    attempt,
                    self._MAX_MODEL_ATTEMPTS,
                    error,
                )

        logger.error(
            "%s failed after %d attempts. Last error: %s",
            stage_name,
            self._MAX_MODEL_ATTEMPTS,
            last_error,
        )
        raise WorkflowError(
            f"{stage_name} failed after {self._MAX_MODEL_ATTEMPTS} "
            f"attempts. Last error: {last_error}"
        ) from last_error

    def _call_interpret_and_plan(
        self,
        current_prompt: str,
        workflow_id: UUID,
        clarification_context: list[tuple[str, str]],
    ) -> IntakeResult | ResearchPlan:
        """Call the planner, tolerating an older keyword-only signature."""

        try:
            return self.research_planner.interpret_and_plan(
                original_prompt=current_prompt,
                workflow_id=workflow_id,
                clarification_context=clarification_context,
            )
        except TypeError as exc:
            if "clarification_context" not in str(exc):
                raise
            return self.research_planner.interpret_and_plan(
                original_prompt=current_prompt,
                workflow_id=workflow_id,
            )

    def run_intake_and_plan(self, original_prompt: str) -> ResearchPlan:
        """Run intake and planning until the request is actionable."""

        workflow_id: UUID = uuid4()
        current_prompt = original_prompt
        clarification_context: list[tuple[str, str]] = []

        while True:
            result = self._run_with_retries(
                "Intake interpretation and planning",
                lambda: self._call_interpret_and_plan(
                    current_prompt,
                    workflow_id,
                    clarification_context,
                ),
            )

            if isinstance(result, ResearchPlan):
                planner_intake = getattr(
                    self.research_planner,
                    "last_intake_result",
                    None,
                )
                if isinstance(planner_intake, IntakeResult):
                    self.last_intake_result = planner_intake
                self.last_research_plan = result
                self._log_research_plan_created(result)
                return result

            if not isinstance(result, IntakeResult):
                raise ValueError(
                    "The planner did not return a valid IntakeResult or "
                    "ResearchPlan."
                )

            self.last_intake_result = result

            if not result.requires_clarification:
                plan = self._run_with_retries(
                    "Research plan generation",
                    lambda: self.research_planner.create_research_plan(
                        intake_result=result,
                    ),
                )
                self.last_research_plan = plan
                self._log_research_plan_created(plan)
                return plan

            logger.info(
                "Intake requires clarification: %d missing field(s).",
                len(result.missing_fields),
            )
            clarification_context = self._resolve_clarification(
                original_prompt=current_prompt,
                intake_result=result,
                workflow_id=workflow_id,
                clarification_context=clarification_context,
            )

    @staticmethod
    def _log_research_plan_created(plan: ResearchPlan) -> None:
        """Log the new plan's scope, including any tickers supplied."""

        candidate_tickers = dict.fromkeys(
            (
                requirement.candidate_name,
                requirement.ticker,
            )
            for requirement in plan.evidence_requirements
            if requirement.candidate_name
        )
        candidate_summary = "; ".join(
            f"{name} (ticker={ticker})" if ticker else f"{name} (no ticker)"
            for name, ticker in candidate_tickers
        ) or "none named"

        logger.info(
            "Research plan created: %d evidence requirement(s), %d "
            "search queries. Candidates: %s.",
            len(plan.evidence_requirements),
            len(plan.search_queries),
            candidate_summary,
        )

    def run_source_selection(
        self,
        research_plan: ResearchPlan,
        additional_research_requests=None,
    ) -> SourceSelection:
        """Execute the source-selection stage for an approved plan."""

        def attempt() -> SourceSelection:
            if additional_research_requests:
                return self.source_selection_agent.search_and_select(
                    research_plan=research_plan,
                    additional_research_requests=additional_research_requests,
                )
            return self.source_selection_agent.search_and_select(
                research_plan=research_plan,
            )

        source_selection = self._run_with_retries(
            "Source selection",
            attempt,
        )
        self.last_source_selection = source_selection
        selected_count = sum(
            1 for selection in source_selection.selections if selection.selected
        )
        logger.info(
            "Source selection completed: status=%s, %d source(s) selected.",
            source_selection.status.value,
            selected_count,
        )
        return source_selection

    def run_extract_evidence(
        self,
        source_selection: SourceSelection,
        research_plan: ResearchPlan,
    ) -> tuple[list[SourceRecord], list[ExtractedEvidence], list[str]]:
        """Run evidence extraction for all selected sources."""

        source_records: list[SourceRecord] = []
        evidence_records: list[ExtractedEvidence] = []
        evidence_gaps: list[str] = []

        for selected_source in source_selection.selections:
            if not selected_source.selected:
                continue

            source_record, extracted, gaps = self._run_with_retries(
                f"Evidence extraction for {selected_source.url}",
                lambda source=selected_source: (
                    self.evidence_extraction_agent.extract_evidence(
                        selected_source=source,
                        evidence_requirements=research_plan.evidence_requirements,
                        workflow_id=source_selection.workflow_id,
                    )
                ),
            )
            source_records.append(source_record)
            evidence_records.extend(extracted)
            evidence_gaps.extend(gaps)

        self.last_source_records = source_records
        self.last_evidence_records = evidence_records
        logger.info(
            "Evidence extraction completed: %d evidence record(s) "
            "extracted from %d source(s), %d gap(s) remaining.",
            len(evidence_records),
            len(source_records),
            len(evidence_gaps),
        )
        return source_records, evidence_records, evidence_gaps

    @staticmethod
    def _research_requests_from_gaps(
        research_plan: ResearchPlan,
        evidence_gaps: list[str],
    ) -> list[AdditionalResearchRequest]:
        """Convert extraction gaps into bounded source-research requests."""

        if not evidence_gaps:
            return []

        candidate_name = (
            research_plan.candidate_names[0]
            if len(research_plan.candidate_names) == 1
            else None
        )
        return [
            AdditionalResearchRequest(
                workflow_id=research_plan.workflow_id,
                requested_by_stage=WorkflowStage.CONTENT_PARSING,
                candidate_name=candidate_name,
                missing_evidence=gap,
                reason=(
                    "The selected source did not yield the required "
                    "structured evidence. Retrieve a source that directly "
                    "reports the missing value."
                ),
                suggested_search_purpose=SearchPurpose.FINANCIAL_GROWTH,
                blocks_recommendation=True,
            )
            for gap in dict.fromkeys(evidence_gaps)
        ]

    def run_financial_analysis(
        self,
        evidence_records: list[ExtractedEvidence],
        evidence_requirements: list[EvidenceRequirement],
        workflow_id: UUID,
    ) -> tuple[list[CalculatedMetric], str, list[ExtractedEvidence], list[SourceRecord]]:
        """Run the financial-analysis stage using extracted evidence.

        The Financial Analysis Agent may fill evidence gaps via
        yfinance before calculating, so this can still produce usable
        evidence even when `evidence_records` started out empty (for
        example, because source selection found no usable sources).

        Returns:
            The accepted calculations, the model's interpretation, the
            evidence list combined with anything yfinance filled in,
            and the source records that new evidence cites. Callers
            must use the returned evidence/source lists downstream
            (for validation and reporting), not the original inputs,
            since those no longer reflect everything that was found.
        """

        calculations, interpretation, new_evidence, new_sources = (
            self.financial_analysis_agent.analyze(
                evidence=evidence_records,
                evidence_requirements=evidence_requirements,
                workflow_id=workflow_id,
            )
        )
        combined_evidence = evidence_records + new_evidence
        self.last_calculations = calculations
        if new_evidence:
            logger.info(
                "Financial analysis filled %d evidence gap(s) via "
                "yfinance.",
                len(new_evidence),
            )
        logger.info(
            "Financial analysis completed: %d calculation(s) produced.",
            len(calculations),
        )
        return calculations, interpretation, combined_evidence, new_sources

    @staticmethod
    def _default_material_risks(research_plan: ResearchPlan) -> list[str]:
        """Disclose the plan's own risk categories as material risks.

        `RecommendationResult` and the deterministic validator both
        require a recommendation to disclose material risks rather
        than silently omit them. The Research Planning Agent already
        identifies relevant risk categories for the request
        (`research_plan.risk_categories`); restating them here keeps
        the disclosure grounded in that plan instead of leaving the
        list empty or inventing candidate-specific risks that were
        never actually evaluated.
        """

        if research_plan.risk_categories:
            return [
                f"Material risk category: {category}."
                for category in research_plan.risk_categories
            ]

        return [
            "This workflow did not identify specific material risk "
            "categories for this request. Review independent sources "
            "for company- and market-specific risks before acting."
        ]

    def _default_candidate_analyses(
        self,
        research_plan: ResearchPlan,
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
    ) -> list[CandidateAnalysis]:
        """Build a minimal, internally consistent analysis set."""

        # Plan-level risk categories apply to every candidate equally
        # and only need computing once; the score-derived risk below
        # is specific to each candidate's own result, so it's computed
        # per candidate inside the loop instead.
        plan_risks = self._default_material_risks(research_plan)
        candidate_names = list(research_plan.candidate_names)
        if not candidate_names:
            candidate_names = [
                evidence.candidate_name
                for evidence in evidence_records
                if evidence.candidate_name
            ]

        candidate_names = list(dict.fromkeys(candidate_names))

        analyses: list[CandidateAnalysis] = []
        for candidate_name in candidate_names:
            supporting_evidence = [
                evidence.evidence_id
                for evidence in evidence_records
                if evidence.candidate_name and evidence.candidate_name.casefold()
                == candidate_name.casefold()
            ]
            calc_ids = [
                calculation.calculation_id
                for calculation in calculations
                if candidate_name.casefold()
                in {name.casefold() for name in calculation.candidate_names}
            ]

            performance_score = (
                self._score_financial_performance(
                    calculations=calculations,
                    candidate_name=candidate_name,
                )
                if calc_ids
                else None
            )
            candidate_material_risks = plan_risks + self._score_derived_risk(
                calculations=calculations,
                candidate_name=candidate_name,
            )

            category = CategoryEvaluation(
                workflow_id=research_plan.workflow_id,
                candidate_name=candidate_name,
                category_name="financial_performance",
                availability_status=(
                    DataAvailabilityStatus.AVAILABLE
                    if calc_ids and supporting_evidence
                    else DataAvailabilityStatus.MISSING
                ),
                score=performance_score,
                calculation_ids=calc_ids,
                supporting_evidence_ids=supporting_evidence,
                opposing_evidence_ids=[],
                rationale="Evidence and calculations were reviewed within the workflow.",
                confidence=(
                    ConfidenceLevel.MODERATE
                    if calc_ids and supporting_evidence
                    else ConfidenceLevel.INSUFFICIENT
                ),
            )

            analyses.append(
                CandidateAnalysis(
                    workflow_id=research_plan.workflow_id,
                    candidate_name=candidate_name,
                    status=(
                        AnalysisStatus.COMPLETED
                        if calc_ids and supporting_evidence
                        else AnalysisStatus.INSUFFICIENT_EVIDENCE
                    ),
                    category_evaluations=[category],
                    calculation_ids=calc_ids,
                    strengths=["Supported by extracted evidence."],
                    weaknesses=[],
                    material_risks=candidate_material_risks,
                    supporting_evidence_ids=supporting_evidence,
                    opposing_evidence_ids=[],
                    missing_information=[],
                    unresolved_conflicts=[],
                    weighted_score=performance_score,
                    confidence=category.confidence,
                    rationale="The candidate was evaluated using available workflow evidence.",
                )
            )

        return analyses

    # Deliberately simple, project-defined bands rather than a
    # universal financial rule (see specs/recommendation-methodology.md
    # section 7) — the goal is a score that reflects what was actually
    # calculated instead of a fixed placeholder, not a rigorous
    # valuation model.
    _GROWTH_SCORE_BANDS: tuple[tuple[Decimal, Decimal], ...] = (
        (Decimal("50"), Decimal("95")),
        (Decimal("15"), Decimal("80")),
        (Decimal("0"), Decimal("60")),
        (Decimal("-15"), Decimal("35")),
    )
    _GROWTH_SCORE_FLOOR = Decimal("15")
    _NO_GROWTH_RATE_SCORE = Decimal("50")

    @staticmethod
    def _growth_rate_for_candidate(
        calculations: list[CalculatedMetric],
        candidate_name: str,
    ) -> Decimal | None:
        """Return a candidate's own calculated growth-rate percent, if any.

        Shared by `_score_financial_performance` and
        `_score_derived_risk` so both read the same result instead of
        two independent lookups drifting apart.
        """

        return next(
            (
                calculation.value
                for calculation in calculations
                if calculation.operation == CalculationOperation.GROWTH_RATE
                and calculation.unit == "percent"
                and candidate_name.casefold()
                in {
                    name.casefold()
                    for name in calculation.candidate_names
                }
            ),
            None,
        )

    @classmethod
    def _score_financial_performance(
        cls,
        calculations: list[CalculatedMetric],
        candidate_name: str,
    ) -> Decimal:
        """Score a candidate from its own calculated growth rate.

        Reflects what was actually found for this candidate instead of
        a fixed placeholder, so two candidates with different results
        don't show the same score. Only a `growth_rate` calculation
        expressed as a percent is used — margin, ratio, and difference
        results aren't on a "higher is better growth" scale, so
        applying growth bands to them would be meaningless; a neutral
        score is used instead of guessing at those.
        """

        growth_rate = cls._growth_rate_for_candidate(
            calculations, candidate_name
        )

        if growth_rate is None:
            return cls._NO_GROWTH_RATE_SCORE

        for threshold, score in cls._GROWTH_SCORE_BANDS:
            if growth_rate >= threshold:
                return score

        return cls._GROWTH_SCORE_FLOOR

    @classmethod
    def _score_derived_risk(
        cls,
        calculations: list[CalculatedMetric],
        candidate_name: str,
    ) -> list[str]:
        """Disclose a candidate's own calculated decline as a risk.

        `_default_material_risks` restates the Research Planning
        Agent's risk categories — decided before any evidence existed,
        the same regardless of what the numbers turn out to be. This
        adds the one thing that can only be known after calculating a
        result: whether the candidate's own growth rate actually
        declined. Returns nothing when growth is flat or positive, or
        when no growth-rate calculation exists to judge — this is a
        disclosure of a specific finding, not a guess.
        """

        growth_rate = cls._growth_rate_for_candidate(
            calculations, candidate_name
        )

        if growth_rate is None or growth_rate >= Decimal("0"):
            return []

        return [
            f"Calculated growth rate of {growth_rate}% indicates a "
            f"decline for {candidate_name} in the periods reviewed."
        ]

    def _default_recommendation(
        self,
        research_plan: ResearchPlan,
        candidate_analyses: list[CandidateAnalysis],
    ) -> RecommendationResult:
        """Build a minimal recommendation consistent with the workflow.

        A candidate may only become the preferred candidate when its
        analysis actually completed with supporting calculations and
        evidence. Candidates that exist but never reached
        `AnalysisStatus.COMPLETED` (for example because the Financial
        Analysis Agent could not produce a valid calculation) must not
        be recommended, per the insufficient-evidence contract on
        `RecommendationResult`.
        """

        completed_analyses = [
            analysis
            for analysis in candidate_analyses
            if analysis.status == AnalysisStatus.COMPLETED
        ]

        missing_information: list[str] = []

        if completed_analyses:
            preferred_candidate = completed_analyses[0].candidate_name
            outcome = RecommendationOutcome.QUALIFIED_RECOMMENDATION
            ranked_candidates = [
                analysis.candidate_name for analysis in completed_analyses
            ]
        elif candidate_analyses:
            preferred_candidate = None
            outcome = RecommendationOutcome.INSUFFICIENT_EVIDENCE
            ranked_candidates = []
            missing_information = [
                "No candidate reached a completed analysis with "
                "supporting calculations and evidence."
            ]
        else:
            preferred_candidate = None
            outcome = RecommendationOutcome.RESEARCH_SHORTLIST
            ranked_candidates = []

        # The preferred candidate's own CandidateAnalysis already
        # carries the combined plan-level and score-derived risks
        # (see _default_candidate_analyses) — reuse it directly so the
        # recommendation and the analysis never disagree about what
        # was disclosed. Without a preferred candidate there's no
        # specific result to draw a score-derived risk from, so this
        # falls back to just the plan-level risk categories.
        recommendation_material_risks = (
            completed_analyses[0].material_risks
            if completed_analyses
            else self._default_material_risks(research_plan)
        )

        return RecommendationResult(
            workflow_id=research_plan.workflow_id,
            outcome=outcome,
            preferred_candidate=preferred_candidate,
            alternative_candidates=[],
            ranked_candidates=ranked_candidates,
            candidate_analysis_ids=[analysis.analysis_id for analysis in candidate_analyses],
            supporting_evidence_ids=[],
            opposing_evidence_ids=[],
            material_risks=recommendation_material_risks,
            missing_information=missing_information,
            unresolved_conflicts=[],
            rationale=(
                "The workflow recommendation is based on the available "
                "evidence and calculations."
                if preferred_candidate is not None
                else "No candidate had a completed analysis backed by "
                "supporting calculations and evidence."
            ),
            confidence=(
                ConfidenceLevel.MODERATE
                if preferred_candidate is not None
                else ConfidenceLevel.INSUFFICIENT
            ),
            human_review_required=True,
        )

    @staticmethod
    def _claim_text_for_evidence(evidence: ExtractedEvidence) -> str:
        """Restate one evidence record's own values as claim text.

        The deterministic validator requires each claim to cite the
        exact source that produced its evidence and to share
        meaningful vocabulary with that evidence's content. Reusing
        the evidence record's own extracted fields (rather than a
        generic, evidence-agnostic sentence) satisfies both checks
        because the same candidate name, value, and period were
        already pulled from that content during extraction.
        """

        candidate = evidence.candidate_name or "The candidate"
        if evidence.reported_value is not None:
            value_text = f"{evidence.reported_value}"
            if evidence.unit:
                value_text += f" {evidence.unit}"
            if evidence.currency:
                value_text += f" {evidence.currency}"
        else:
            value_text = evidence.evidence_type

        period_text = (
            f" for {evidence.reporting_period}"
            if evidence.reporting_period
            else ""
        )

        return f"{candidate} reported {value_text}{period_text}."

    def _default_validation_claims(
        self,
        research_plan: ResearchPlan,
        source_records: list[SourceRecord],
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
    ) -> list[ValidationClaim]:
        """Create one grounded validation claim per evidence record and
        calculation, rather than one generic claim per source.

        Each evidence-level claim cites exactly the source that
        produced its evidence, so it cannot fail the citation-match
        check by pulling in evidence extracted from a different
        source. Each calculation-level claim cites exactly the
        evidence the calculation used, with claim text built from
        those same evidence records, so both the calculation-lineage
        check and the lexical-support check pass on real data.
        """

        evidence_by_id = {
            evidence.evidence_id: evidence
            for evidence in evidence_records
        }

        claims: list[ValidationClaim] = [
            ValidationClaim(
                workflow_id=research_plan.workflow_id,
                text=self._claim_text_for_evidence(evidence),
                candidate_name=evidence.candidate_name,
                source_ids=[evidence.source_id],
                evidence_ids=[evidence.evidence_id],
            )
            for evidence in evidence_records
            if evidence.candidate_name
        ]

        for calculation in calculations:
            input_evidence = [
                evidence_by_id[evidence_id]
                for evidence_id in calculation.input_evidence_ids
                if evidence_id in evidence_by_id
            ]
            if len(input_evidence) != len(calculation.input_evidence_ids):
                continue

            source_ids = list(
                dict.fromkeys(
                    evidence.source_id for evidence in input_evidence
                )
            )
            calculation_text = " ".join(
                self._claim_text_for_evidence(evidence)
                for evidence in input_evidence
            ) + (
                f" The calculated {calculation.metric_name} was "
                f"{calculation.value}"
                f"{f' {calculation.unit}' if calculation.unit else ''}."
            )

            # Only attach a single candidate name when every input
            # evidence record agrees on it (the common case). A
            # difference calculation may legitimately compare two
            # different candidates, and attaching one candidate's name
            # to a claim covering the other candidate's evidence would
            # trip the "cited evidence belongs to another candidate"
            # check on a perfectly valid cross-candidate comparison.
            calculation_candidate_name = (
                calculation.candidate_names[0]
                if len(set(calculation.candidate_names)) == 1
                else None
            )

            claims.append(
                ValidationClaim(
                    workflow_id=research_plan.workflow_id,
                    text=calculation_text,
                    candidate_name=calculation_candidate_name,
                    source_ids=source_ids,
                    evidence_ids=list(calculation.input_evidence_ids),
                    calculation_id=calculation.calculation_id,
                    expected_value=calculation.value,
                    expected_unit=calculation.unit,
                    expected_currency=calculation.currency,
                    expected_reporting_periods=calculation.reporting_periods,
                )
            )

        return claims

    def run_evidence_validation(
        self,
        research_plan: ResearchPlan,
        source_records: list[SourceRecord],
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
    ) -> ValidationResult:
        """Run the validation stage for the generated recommendation."""

        if self.evidence_validation_agent is None:
            raise ValueError("Evidence validation agent is not configured.")

        intake_result = self.last_intake_result
        if intake_result is None:
            raise ValueError("No validated intake result is available.")

        candidate_analyses = self._default_candidate_analyses(
            research_plan=research_plan,
            evidence_records=evidence_records,
            calculations=calculations,
        )
        recommendation = self._default_recommendation(
            research_plan=research_plan,
            candidate_analyses=candidate_analyses,
        )
        # Report generation must validate the exact same recommendation
        # and candidate-analysis records that were just checked here, not
        # freshly rebuilt look-alikes with new random identifiers. Cache
        # them so run_report_generation reuses these instances instead of
        # calling the _default_* builders again.
        self.last_candidate_analyses = candidate_analyses
        self.last_recommendation = recommendation
        claims = self._default_validation_claims(
            research_plan=research_plan,
            source_records=source_records,
            evidence_records=evidence_records,
            calculations=calculations,
        )

        validation_result = self.evidence_validation_agent.validate(
            research_request=intake_result.research_request,
            investor_profile=intake_result.investor_profile,
            research_plan=research_plan,
            source_records=source_records,
            evidence_records=evidence_records,
            calculations=calculations,
            candidate_analyses=candidate_analyses,
            recommendation=recommendation,
            claims=claims,
        )
        self.last_validation_result = validation_result
        if validation_result.outcome.value == "approved":
            logger.info(
                "Evidence validation approved: %s",
                validation_result.summary,
            )
        else:
            logger.warning(
                "Evidence validation failed: outcome=%s, %d finding(s). %s",
                validation_result.outcome.value,
                len(validation_result.findings),
                validation_result.summary,
            )
        return validation_result

    def run_report_generation(
        self,
        research_plan: ResearchPlan,
        validation_result: ValidationResult,
        source_records: list[SourceRecord],
        evidence_records: list[ExtractedEvidence],
        calculations: list[CalculatedMetric],
    ) -> ReportArtifact:
        """Generate, validate, and write the report from approved data.

        The Report Writing Agent owns its own report-writer tool and
        calls it directly as part of generating the report, so this
        method's single retry-wrapped call covers drafting and writing
        together. There is no separate write step afterward.
        """

        if self.report_agent is None:
            raise ValueError("Report agent is not configured.")

        intake_result = self.last_intake_result
        if intake_result is None:
            raise ValueError("No intake result is available for report generation.")

        # Reuse the exact candidate-analysis and recommendation records
        # that evidence validation just approved. Rebuilding fresh ones
        # here would produce different random recommendation_id and
        # analysis_id values than what validation actually checked, which
        # the report-writing tool correctly refuses to accept.
        recommendation = self.last_recommendation
        candidate_analyses = self.last_candidate_analyses
        if recommendation is None:
            raise ValueError(
                "Report generation requires a completed evidence "
                "validation pass with a cached recommendation."
            )

        report_draft, report_artifact = self._run_with_retries(
            "Report generation",
            lambda: self.report_agent.generate_report(
                research_request=intake_result.research_request,
                investor_profile=intake_result.investor_profile,
                research_scope=intake_result.research_scope,
                research_plan=research_plan,
                source_records=source_records,
                evidence_records=evidence_records,
                calculations=calculations,
                candidate_analyses=candidate_analyses,
                recommendation_result=recommendation,
                validation_result=validation_result,
            ),
        )
        self.last_report_draft = report_draft
        self.last_report_artifact = report_artifact
        logger.info(
            "Report written: %s (outcome=%s).",
            report_artifact.relative_path,
            report_draft.recommendation_outcome.value,
        )
        return report_artifact

    def run(self, original_prompt: str) -> tuple[ResearchPlan, SourceSelection]:
        """Execute the full Phase 9 workflow while keeping the original return contract."""

        logger.info("Workflow started for request: %s", original_prompt)

        research_plan = self.run_intake_and_plan(original_prompt)
        source_selection = self.run_source_selection(research_plan)
        source_records: list[SourceRecord] = []
        evidence_records: list[ExtractedEvidence] = []
        for attempt in range(2):
            (
                round_source_records,
                round_evidence_records,
                evidence_gaps,
            ) = self.run_extract_evidence(
                source_selection=source_selection,
                research_plan=research_plan,
            )
            # A retry targets a specific validation finding or gap, not
            # a restart, so evidence already gathered (and, for
            # anything the model already accepted, already valid) in
            # an earlier round must carry forward rather than being
            # discarded when this round only re-searches for what's
            # still missing.
            source_records = source_records + round_source_records
            evidence_records = evidence_records + round_evidence_records
            (
                calculations,
                _,
                evidence_records,
                new_sources,
            ) = self.run_financial_analysis(
                evidence_records=evidence_records,
                evidence_requirements=research_plan.evidence_requirements,
                workflow_id=research_plan.workflow_id,
            )
            # run_financial_analysis may have filled gaps via yfinance,
            # so evidence_records above is now the combined list, and
            # any new source records it cites need to join the
            # workflow's own source list before validation checks
            # citations against it.
            source_records = source_records + new_sources
            self.last_source_records = source_records
            self.last_evidence_records = evidence_records

            if self.last_intake_result is None:
                break

            validation_result = self.run_evidence_validation(
                research_plan=research_plan,
                source_records=source_records,
                evidence_records=evidence_records,
                calculations=calculations,
            )

            research_requests = [
                *self._research_requests_from_gaps(
                    research_plan=research_plan,
                    evidence_gaps=evidence_gaps,
                ),
                *validation_result.additional_research_requests,
            ]

            if (
                research_requests
                and attempt == 0
            ):
                source_selection = self.run_source_selection(
                    research_plan=research_plan,
                    additional_research_requests=research_requests,
                )
                continue

            if validation_result.outcome.value != "approved":
                logger.info(
                    "Workflow terminated without a report: validation "
                    "did not approve the result."
                )
                break

            self.run_report_generation(
                research_plan=research_plan,
                validation_result=validation_result,
                source_records=source_records,
                evidence_records=evidence_records,
                calculations=calculations,
            )
            logger.info("Workflow completed successfully.")
            break

        return research_plan, source_selection
