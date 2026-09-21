"""Tests for the Phase 9 orchestrator boundary."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fin_automation.models.common import (
    AnalysisStatus,
    ConfidenceLevel,
    DataAvailabilityStatus,
    RecommendationOutcome,
    SearchPurpose,
    SourceCategory,
    SourceSelectionStatus,
    WorkflowStage,
)
from fin_automation.models.financial import (
    CalculatedMetric,
    CandidateAnalysis,
    CategoryEvaluation,
    RecommendationResult,
)
from fin_automation.models.intake import (
    IntakeResult,
    InvestorProfile,
    ResearchRequest,
    ResearchScope,
)
from fin_automation.models.research import (
    AdditionalResearchRequest,
    EvidenceRequirement,
    ResearchPlan,
    SearchQuery,
)
from fin_automation.models.reports import ReportArtifact, ReportDraft
from fin_automation.models.sources import (
    ExtractedEvidence,
    SelectedSource,
    SourceRecord,
    SourceSelection,
)
from fin_automation.models.validation import ValidationResult
from fin_automation.workflow.orchestrator import ResearchOrchestrator


class DummyPlanner:
    def __init__(self, plan, intake_result=None):
        self._plan = plan
        self._intake_result = intake_result

    def interpret_and_plan(
        self,
        original_prompt: str,
        workflow_id,
        clarification_context=None,
    ):
        if self._intake_result is not None:
            return self._intake_result
        return self._plan

    def create_research_plan(self, intake_result):
        return self._plan


class DummySourceSelectionAgent:
    def __init__(self):
        self.called_with = None

    def search_and_select(self, research_plan):

        self.called_with = research_plan
        requirement = research_plan.evidence_requirements[0]
        return SourceSelection(
            workflow_id=research_plan.workflow_id,
            plan_id=research_plan.plan_id,
            status=SourceSelectionStatus.READY_FOR_RETRIEVAL,
            selections=[
                SelectedSource(
                    search_result_id=uuid4(),
                    url="https://example.com/source",
                    title="Example source",
                    domain="example.com",
                    raw_content="Example content.",
                    candidate_name="Example Inc",
                    selected=True,
                    expected_source_category=SourceCategory.PRIMARY,
                    selection_reason="Relevant to revenue growth.",
                    evidence_requirement_ids=[requirement.requirement_id],
                )
            ],
            uncovered_evidence_requirement_ids=[],
            additional_research_requests=[],
        )


class DummyEvidenceExtractionAgent:
    def extract_evidence(self, selected_source, evidence_requirements, workflow_id):
        source_record = SourceRecord(
            workflow_id=workflow_id,
            search_result_id=selected_source.search_result_id,
            title=selected_source.title,
            url=selected_source.url,
            retrieval_date=__import__("datetime").date.today(),
            source_category=selected_source.expected_source_category,
            parsing_status="success",
            candidate_names=[selected_source.candidate_name] if selected_source.candidate_name else [],
            evidence_requirement_ids=selected_source.evidence_requirement_ids,
            content_summary="Example source content.",
        )
        current = ExtractedEvidence(
            workflow_id=workflow_id,
            source_id=source_record.source_id,
            candidate_name="Example Inc",
            evidence_requirement_id=evidence_requirements[0].requirement_id,
            evidence_type="revenue",
            content="Example Inc reported FY2025 revenue of 110 billion USD.",
            reported_value=Decimal("110"),
            currency="USD",
            unit="billion",
            reporting_period="FY2025",
        )
        previous = ExtractedEvidence(
            workflow_id=workflow_id,
            source_id=source_record.source_id,
            candidate_name="Example Inc",
            evidence_requirement_id=evidence_requirements[0].requirement_id,
            evidence_type="revenue",
            content="Example Inc reported FY2024 revenue of 100 billion USD.",
            reported_value=Decimal("100"),
            currency="USD",
            unit="billion",
            reporting_period="FY2024",
        )
        return source_record, [current, previous], []


class DummyFinancialAnalysisAgent:
    def analyze(self, evidence, evidence_requirements, workflow_id):
        current, previous = evidence[:2]
        return (
            [
                CalculatedMetric(
                    workflow_id=workflow_id,
                    operation="growth_rate",
                    metric_name="revenue growth",
                    candidate_names=["Example Inc"],
                    value=Decimal("10.00"),
                    unit="percent",
                    currency="USD",
                    input_evidence_ids=[current.evidence_id, previous.evidence_id],
                    formula="((current - prior) / prior) * 100",
                    reporting_periods=["FY2024", "FY2025"],
                )
            ],
            "analysis complete",
            # No new evidence/sources in this dummy: real gap-filling
            # is exercised by the FinancialDataTool/agent tests instead.
            [],
            [],
        )


class DummyEvidenceValidationAgent:
    def validate(self, **kwargs):
        return ValidationResult(
            workflow_id=kwargs["research_request"].workflow_id,
            recommendation_id=kwargs["recommendation"].recommendation_id,
            outcome="approved",
            findings=[],
            approved_candidate_analysis_ids=[analysis.analysis_id for analysis in kwargs["candidate_analyses"]],
            approved_source_ids=[source.source_id for source in kwargs["source_records"]],
            approved_evidence_ids=[evidence.evidence_id for evidence in kwargs["evidence_records"]],
            approved_calculation_ids=[calculation.calculation_id for calculation in kwargs["calculations"]],
            summary="Validated.",
        )


class DummyReportAgent:
    def generate_report(self, **kwargs):
        report_draft = ReportDraft(
            workflow_id=kwargs["research_request"].workflow_id,
            validation_id=kwargs["validation_result"].validation_id,
            recommendation_id=kwargs["recommendation_result"].recommendation_id,
            report_type="research_report",
            recommendation_outcome=RecommendationOutcome.QUALIFIED_RECOMMENDATION,
            preferred_candidate="Example Inc",
            title="Example Inc research brief",
            markdown_content="# Research Question\n\nExample research question.\n\n# Investor Profile\n\nModerate growth investor.\n\n# Research Scope\n\nSingle-company analysis.\n\n# Executive Summary\n\nExample summary.\n\n# Research Methodology\n\nSource and evidence review.\n\n# Candidate Analyses\n\nCandidate analysis included.\n\n# Candidate Comparison\n\nComparison summary.\n\n# Recommendation Outcome\n\nRecommended candidate is Example Inc.\n\n# Material Risks\n\nNo material risks noted.\n\n# Missing Information and Unresolved Conflicts\n\nNone.\n\n# Limitations\n\nLimited evidence.\n\n# Sources\n\nExample source.\n\n# Human Review\n\nHuman review is required before acting on this recommendation.",
            risks=["Market risk."],
            limitations=["Limited evidence."],
            human_review_statement="Human review is required before acting on this recommendation.",
            candidate_analysis_ids=[
                analysis.analysis_id for analysis in kwargs["candidate_analyses"]
            ],
            source_ids=[source.source_id for source in kwargs["source_records"]],
            evidence_ids=[evidence.evidence_id for evidence in kwargs["evidence_records"]],
            calculation_ids=[calculation.calculation_id for calculation in kwargs["calculations"]],
        )
        # The real ReportAgent now owns its writer tool and returns both
        # the validated draft and the artifact the tool produced, since
        # the orchestrator no longer calls a separate write step.
        report_artifact = ReportArtifact(
            workflow_id=report_draft.workflow_id,
            report_draft_id=report_draft.report_draft_id,
            artifact_type="markdown_report",
            status="created",
            file_name="report1.md",
            relative_path="outputs/report1.md",
            created_at=datetime.now(timezone.utc),
        )
        return report_draft, report_artifact


def make_plan() -> ResearchPlan:
    requirement = EvidenceRequirement(
        name="Revenue growth",
        description="Find revenue growth evidence.",
        candidate_name="Example Inc",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.PRIMARY],
        required=True,
    )
    return ResearchPlan(
        workflow_id=uuid4(),
        research_objective="Compare revenue growth.",
        candidate_discovery_required=False,
        candidate_names=["Example Inc"],
        comparison_criteria=["revenue growth"],
        risk_categories=["market competition"],
        evidence_requirements=[requirement],
        search_queries=[
            SearchQuery(
                query="Example Inc revenue growth",
                purpose=SearchPurpose.FINANCIAL_GROWTH,
                candidate_name="Example Inc",
                evidence_requirement_ids=[requirement.requirement_id],
            )
        ],
        preferred_source_categories=[SourceCategory.PRIMARY],
        candidate_limit=1,
        source_limit_per_candidate=3,
        assumptions=[],
    )


def make_intake_result(workflow_id: str) -> IntakeResult:
    request = ResearchRequest(
        workflow_id=workflow_id,
        original_prompt="Research Example Inc.",
        research_question="Should Example Inc be researched?",
        request_type="single_candidate_analysis",
    )
    profile = InvestorProfile(
        workflow_id=workflow_id,
        risk_tolerance="moderate",
        investment_objective="growth",
        time_horizon="long_term",
    )
    scope = ResearchScope(
        workflow_id=workflow_id,
        asset_types=["public_stock"],
        named_candidates=["Example Inc"],
        candidate_limit=1,
    )
    return IntakeResult(
        workflow_id=workflow_id,
        research_request=request,
        investor_profile=profile,
        research_scope=scope,
        assumptions=[],
        missing_fields=[],
        requires_clarification=False,
        clarification_questions=[],
    )


def test_orchestrator_runs_source_selection_on_approved_plan() -> None:
    plan = make_plan()
    dummy_planner = DummyPlanner(plan)
    dummy_source_agent = DummySourceSelectionAgent()

    orchestrator = ResearchOrchestrator(
        research_planner=dummy_planner,
        source_selection_agent=dummy_source_agent,
        evidence_extraction_agent=DummyEvidenceExtractionAgent(),
        financial_analysis_agent=DummyFinancialAnalysisAgent(),
        evidence_validation_agent=DummyEvidenceValidationAgent(),
        report_agent=DummyReportAgent(),
    )

    returned_plan, result = orchestrator.run("Research Example Inc")

    assert returned_plan == plan
    assert dummy_source_agent.called_with == plan
    assert result.workflow_id == plan.workflow_id
    assert orchestrator.last_research_plan == plan
    assert orchestrator.last_source_selection is not None


def test_orchestrator_executes_full_phase_9_pipeline() -> None:
    plan = make_plan()
    intake_result = make_intake_result(str(plan.workflow_id))
    dummy_planner = DummyPlanner(plan, intake_result=intake_result)
    dummy_source_agent = DummySourceSelectionAgent()

    orchestrator = ResearchOrchestrator(
        research_planner=dummy_planner,
        source_selection_agent=dummy_source_agent,
        evidence_extraction_agent=DummyEvidenceExtractionAgent(),
        financial_analysis_agent=DummyFinancialAnalysisAgent(),
        evidence_validation_agent=DummyEvidenceValidationAgent(),
        report_agent=DummyReportAgent(),
    )

    returned_plan, result = orchestrator.run("Research Example Inc")

    assert returned_plan == plan
    assert result.workflow_id == plan.workflow_id
    assert len(orchestrator.last_evidence_records) == 2
    assert len(orchestrator.last_calculations) == 1
    assert orchestrator.last_validation_result is not None
    assert orchestrator.last_report_draft is not None
    assert orchestrator.last_report_artifact is not None


def _growth_calculation(*, value: str, candidate="Example Inc") -> CalculatedMetric:
    return CalculatedMetric(
        workflow_id=uuid4(),
        operation="growth_rate",
        metric_name="revenue growth",
        candidate_names=[candidate],
        value=Decimal(value),
        unit="percent",
        currency="USD",
        input_evidence_ids=[uuid4(), uuid4()],
        formula="((current - prior) / prior) * 100",
        reporting_periods=["FY2023", "FY2024"],
    )


def test_score_financial_performance_rewards_strong_growth() -> None:
    score = ResearchOrchestrator._score_financial_performance(
        calculations=[_growth_calculation(value="126.39")],
        candidate_name="Example Inc",
    )

    assert score == Decimal("95")


def test_score_financial_performance_penalizes_decline() -> None:
    score = ResearchOrchestrator._score_financial_performance(
        calculations=[_growth_calculation(value="-43.53")],
        candidate_name="Example Inc",
    )

    assert score == Decimal("15")


def test_score_financial_performance_differs_by_growth_band() -> None:
    strong = ResearchOrchestrator._score_financial_performance(
        calculations=[_growth_calculation(value="60")],
        candidate_name="Example Inc",
    )
    modest = ResearchOrchestrator._score_financial_performance(
        calculations=[_growth_calculation(value="2.09")],
        candidate_name="Example Inc",
    )
    mild_decline = ResearchOrchestrator._score_financial_performance(
        calculations=[_growth_calculation(value="-5")],
        candidate_name="Example Inc",
    )

    assert strong > modest > mild_decline


def test_score_financial_performance_ignores_other_candidates_calculation() -> None:
    score = ResearchOrchestrator._score_financial_performance(
        calculations=[_growth_calculation(value="126.39", candidate="Other Inc")],
        candidate_name="Example Inc",
    )

    assert score == ResearchOrchestrator._NO_GROWTH_RATE_SCORE


def test_score_financial_performance_neutral_for_non_percent_operation() -> None:
    calculation = CalculatedMetric(
        workflow_id=uuid4(),
        operation="difference",
        metric_name="revenue difference",
        candidate_names=["Example Inc"],
        value=Decimal("36.70"),
        unit="billion",
        currency="USD",
        input_evidence_ids=[uuid4(), uuid4()],
        formula="first - second",
        reporting_periods=["FY2024"],
    )

    score = ResearchOrchestrator._score_financial_performance(
        calculations=[calculation],
        candidate_name="Example Inc",
    )

    assert score == ResearchOrchestrator._NO_GROWTH_RATE_SCORE


def test_score_derived_risk_flags_declining_growth() -> None:
    risks = ResearchOrchestrator._score_derived_risk(
        calculations=[_growth_calculation(value="-12.4")],
        candidate_name="Example Inc",
    )

    assert len(risks) == 1
    assert "-12.4%" in risks[0]
    assert "Example Inc" in risks[0]


def test_score_derived_risk_silent_for_positive_growth() -> None:
    risks = ResearchOrchestrator._score_derived_risk(
        calculations=[_growth_calculation(value="2.09")],
        candidate_name="Example Inc",
    )

    assert risks == []


def test_score_derived_risk_silent_for_zero_growth() -> None:
    risks = ResearchOrchestrator._score_derived_risk(
        calculations=[_growth_calculation(value="0")],
        candidate_name="Example Inc",
    )

    assert risks == []


def test_score_derived_risk_silent_when_no_growth_rate_calculated() -> None:
    risks = ResearchOrchestrator._score_derived_risk(
        calculations=[],
        candidate_name="Example Inc",
    )

    assert risks == []


def test_score_derived_risk_ignores_other_candidates_calculation() -> None:
    risks = ResearchOrchestrator._score_derived_risk(
        calculations=[_growth_calculation(value="-50", candidate="Other Inc")],
        candidate_name="Example Inc",
    )

    assert risks == []

