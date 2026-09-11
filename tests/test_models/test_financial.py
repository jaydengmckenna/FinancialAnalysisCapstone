"""Tests for financial calculation and analysis contracts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fin_automation.models.common import (
    AnalysisStatus,
    CalculationStatus,
    CalculationType,
    ConfidenceLevel,
    DataAvailabilityStatus,
    RecommendationOutcome,
)
from fin_automation.models.financial import (
    CalculationRecord,
    CandidateAnalysis,
    CategoryEvaluation,
    FinancialInput,
    RecommendationResult,
)


def create_category_evaluation(
    workflow_id: UUID,
    candidate_name: str = "Company A",
    category_name: str = "financial growth",
) -> CategoryEvaluation:
    """Create a valid category evaluation."""

    return CategoryEvaluation(
        workflow_id=workflow_id,
        candidate_name=candidate_name,
        category_name=category_name,
        availability_status=DataAvailabilityStatus.AVAILABLE,
        score=Decimal("82.5"),
        calculation_ids=[uuid4()],
        supporting_evidence_ids=[uuid4()],
        opposing_evidence_ids=[uuid4()],
        risks=["Revenue growth may slow."],
        missing_information=[],
        rationale=(
            "Revenue growth is supported by the reported results."
        ),
        confidence=ConfidenceLevel.MODERATE,
    )


def test_available_financial_input_accepts_value() -> None:
    """Available financial input should preserve its value."""

    financial_input = FinancialInput(
        workflow_id=uuid4(),
        candidate_name="Company A",
        metric_name="revenue",
        value=Decimal("2500000000"),
        currency="usd",
        unit="currency_units",
        reporting_period="FY2025",
        availability_status=DataAvailabilityStatus.AVAILABLE,
        evidence_id=uuid4(),
    )

    assert financial_input.value == Decimal("2500000000")
    assert financial_input.currency == "USD"


def test_available_financial_input_requires_value() -> None:
    """Available financial data requires a numeric value."""

    with pytest.raises(
        ValidationError,
        match="requires a numeric value",
    ):
        FinancialInput(
            workflow_id=uuid4(),
            candidate_name="Company A",
            metric_name="revenue",
            reporting_period="FY2025",
            availability_status=DataAvailabilityStatus.AVAILABLE,
            evidence_id=uuid4(),
        )


def test_missing_financial_input_rejects_value() -> None:
    """Missing financial data cannot contain a usable value."""

    with pytest.raises(
        ValidationError,
        match="cannot contain a usable numeric value",
    ):
        FinancialInput(
            workflow_id=uuid4(),
            candidate_name="Company A",
            metric_name="revenue",
            value=Decimal("100"),
            reporting_period="FY2025",
            availability_status=DataAvailabilityStatus.MISSING,
            evidence_id=uuid4(),
        )


def test_financial_input_normalizes_currency() -> None:
    """Currency codes should be normalized to uppercase."""

    financial_input = FinancialInput(
        workflow_id=uuid4(),
        candidate_name="Company A",
        metric_name="revenue",
        value=Decimal("100"),
        currency="usd",
        reporting_period="FY2025",
        availability_status=DataAvailabilityStatus.AVAILABLE,
        evidence_id=uuid4(),
    )

    assert financial_input.currency == "USD"


def test_financial_input_rejects_invalid_currency() -> None:
    """Currency should use a three-character code."""

    with pytest.raises(
        ValidationError,
        match="three-character code",
    ):
        FinancialInput(
            workflow_id=uuid4(),
            candidate_name="Company A",
            metric_name="revenue",
            value=Decimal("100"),
            currency="US",
            reporting_period="FY2025",
            availability_status=DataAvailabilityStatus.AVAILABLE,
            evidence_id=uuid4(),
        )


def test_completed_calculation_accepts_result() -> None:
    """Completed calculation should preserve its result."""

    calculation = CalculationRecord(
        workflow_id=uuid4(),
        candidate_name="Company A",
        calculation_type=CalculationType.REVENUE_GROWTH,
        status=CalculationStatus.COMPLETED,
        formula_name="revenue_growth_percentage",
        input_ids=[uuid4(), uuid4()],
        result=Decimal("12.50"),
        result_unit="percent",
        reporting_period="FY2024 to FY2025",
    )

    assert calculation.result == Decimal("12.50")
    assert calculation.status == CalculationStatus.COMPLETED


def test_completed_calculation_requires_result() -> None:
    """Completed calculation requires a numeric result."""

    with pytest.raises(
        ValidationError,
        match="requires a numeric result",
    ):
        CalculationRecord(
            workflow_id=uuid4(),
            candidate_name="Company A",
            calculation_type=CalculationType.REVENUE_GROWTH,
            status=CalculationStatus.COMPLETED,
            formula_name="revenue_growth_percentage",
            input_ids=[uuid4(), uuid4()],
        )


def test_completed_calculation_requires_inputs() -> None:
    """Completed calculation requires traceable inputs."""

    with pytest.raises(
        ValidationError,
        match="requires at least one input",
    ):
        CalculationRecord(
            workflow_id=uuid4(),
            candidate_name="Company A",
            calculation_type=CalculationType.REVENUE_GROWTH,
            status=CalculationStatus.COMPLETED,
            formula_name="revenue_growth_percentage",
            input_ids=[],
            result=Decimal("10"),
        )


def test_calculation_rejects_duplicate_inputs() -> None:
    """Calculation inputs should not contain duplicate references."""

    input_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="input identifiers must be unique",
    ):
        CalculationRecord(
            workflow_id=uuid4(),
            candidate_name="Company A",
            calculation_type=CalculationType.REVENUE_GROWTH,
            status=CalculationStatus.COMPLETED,
            formula_name="revenue_growth_percentage",
            input_ids=[input_id, input_id],
            result=Decimal("10"),
        )


@pytest.mark.parametrize(
    "status",
    [
        CalculationStatus.MISSING_INPUT,
        CalculationStatus.INVALID_INPUT,
        CalculationStatus.NOT_APPLICABLE,
        CalculationStatus.FAILED,
    ],
)

def test_incomplete_calculation_rejects_result(
    status: CalculationStatus,
) -> None:
    """Incomplete calculations cannot contain usable results."""

    with pytest.raises(
        ValidationError,
        match="cannot contain a usable result",
    ):
        CalculationRecord(
            workflow_id=uuid4(),
            candidate_name="Company A",
            calculation_type=CalculationType.PRICE_TO_EARNINGS,
            status=status,
            formula_name="price_to_earnings",
            input_ids=[uuid4()],
            result=Decimal("10"),
        )


def test_candidate_calculation_requires_candidate_name() -> None:
    """Candidate-level calculations require a candidate."""

    with pytest.raises(
        ValidationError,
        match="Candidate name is required",
    ):
        CalculationRecord(
            workflow_id=uuid4(),
            calculation_type=CalculationType.NET_PROFIT_MARGIN,
            status=CalculationStatus.COMPLETED,
            formula_name="net_profit_margin",
            input_ids=[uuid4(), uuid4()],
            result=Decimal("15"),
        )


def test_weighted_score_may_omit_candidate_name() -> None:
    """Workflow-level weighted score may omit a candidate name."""

    calculation = CalculationRecord(
        workflow_id=uuid4(),
        calculation_type=CalculationType.WEIGHTED_SCORE,
        status=CalculationStatus.COMPLETED,
        formula_name="weighted_candidate_score",
        input_ids=[uuid4()],
        result=Decimal("82.5"),
        result_unit="score",
    )

    assert calculation.candidate_name is None
    assert calculation.result == Decimal("82.5")


def test_calculation_rejects_naive_timestamp() -> None:
    """Calculation timestamps must be timezone-aware."""

    with pytest.raises(
        ValidationError,
        match="created_at must be timezone-aware",
    ):
        CalculationRecord(
            workflow_id=uuid4(),
            candidate_name="Company A",
            calculation_type=CalculationType.REVENUE_GROWTH,
            status=CalculationStatus.COMPLETED,
            formula_name="revenue_growth_percentage",
            input_ids=[uuid4(), uuid4()],
            result=Decimal("10"),
            created_at=datetime(2026, 9, 11, 10, 0, 0),
        )


def test_available_category_accepts_score() -> None:
    """Available category evaluation should accept a valid score."""

    evaluation = create_category_evaluation(uuid4())

    assert evaluation.score == Decimal("82.5")
    assert (
        evaluation.availability_status
        == DataAvailabilityStatus.AVAILABLE
    )


def test_available_category_requires_score() -> None:
    """Available category evaluation requires a score."""

    with pytest.raises(
        ValidationError,
        match="requires a score",
    ):
        CategoryEvaluation(
            workflow_id=uuid4(),
            candidate_name="Company A",
            category_name="profitability",
            availability_status=DataAvailabilityStatus.AVAILABLE,
            rationale="Profitability evidence was collected.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_missing_category_rejects_low_substitute_score() -> None:
    """Missing data cannot be represented by a low score."""

    with pytest.raises(
        ValidationError,
        match="cannot receive a score",
    ):
        CategoryEvaluation(
            workflow_id=uuid4(),
            candidate_name="Company A",
            category_name="valuation",
            availability_status=DataAvailabilityStatus.MISSING,
            score=Decimal("0"),
            missing_information=["Current valuation data"],
            rationale="Current valuation evidence is missing.",
            confidence=ConfidenceLevel.INSUFFICIENT,
        )


@pytest.mark.parametrize(
    "invalid_score",
    [
        Decimal("-1"),
        Decimal("101"),
    ],
)
def test_category_rejects_out_of_range_score(
    invalid_score: Decimal,
) -> None:
    """Category scores must remain between zero and one hundred."""

    with pytest.raises(ValidationError):
        CategoryEvaluation(
            workflow_id=uuid4(),
            candidate_name="Company A",
            category_name="profitability",
            availability_status=DataAvailabilityStatus.AVAILABLE,
            score=invalid_score,
            rationale="Profitability evaluation.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_category_rejects_duplicate_references() -> None:
    """Category identifier lists should reject duplicates."""

    evidence_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="Referenced identifiers must be unique",
    ):
        CategoryEvaluation(
            workflow_id=uuid4(),
            candidate_name="Company A",
            category_name="profitability",
            availability_status=DataAvailabilityStatus.AVAILABLE,
            score=Decimal("75"),
            supporting_evidence_ids=[
                evidence_id,
                evidence_id,
            ],
            rationale="Profitability evaluation.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_available_category_rejects_insufficient_confidence() -> None:
    """Available category should not use insufficient confidence."""

    with pytest.raises(
        ValidationError,
        match="cannot use insufficient confidence",
    ):
        CategoryEvaluation(
            workflow_id=uuid4(),
            candidate_name="Company A",
            category_name="profitability",
            availability_status=DataAvailabilityStatus.AVAILABLE,
            score=Decimal("75"),
            rationale="Profitability evaluation.",
            confidence=ConfidenceLevel.INSUFFICIENT,
        )


def test_completed_candidate_analysis_accepts_evaluation() -> None:
    """Completed candidate analysis requires category evaluation."""

    workflow_id = uuid4()
    evaluation = create_category_evaluation(workflow_id)

    analysis = CandidateAnalysis(
        workflow_id=workflow_id,
        candidate_name="Company A",
        status=AnalysisStatus.COMPLETED,
        category_evaluations=[evaluation],
        calculation_ids=evaluation.calculation_ids,
        strengths=["Strong revenue growth."],
        weaknesses=["High valuation."],
        material_risks=["Revenue growth may slow."],
        supporting_evidence_ids=(
            evaluation.supporting_evidence_ids
        ),
        opposing_evidence_ids=(
            evaluation.opposing_evidence_ids
        ),
        weighted_score=Decimal("82.5"),
        confidence=ConfidenceLevel.MODERATE,
        rationale=(
            "Company A is supported by the available evidence."
        ),
    )

    assert analysis.status == AnalysisStatus.COMPLETED
    assert analysis.weighted_score == Decimal("82.5")


def test_completed_analysis_requires_evaluation() -> None:
    """Completed analysis requires category-level evaluation."""

    with pytest.raises(
        ValidationError,
        match="requires at least one category evaluation",
    ):
        CandidateAnalysis(
            workflow_id=uuid4(),
            candidate_name="Company A",
            status=AnalysisStatus.COMPLETED,
            category_evaluations=[],
            confidence=ConfidenceLevel.MODERATE,
            rationale="Candidate analysis.",
        )


def test_analysis_rejects_mismatched_workflow() -> None:
    """Nested evaluations must belong to the same workflow."""

    with pytest.raises(
        ValidationError,
        match="must use the same workflow_id",
    ):
        CandidateAnalysis(
            workflow_id=uuid4(),
            candidate_name="Company A",
            status=AnalysisStatus.COMPLETED,
            category_evaluations=[
                create_category_evaluation(uuid4())
            ],
            confidence=ConfidenceLevel.MODERATE,
            rationale="Candidate analysis.",
        )


def test_analysis_rejects_wrong_candidate_evaluation() -> None:
    """Nested evaluations must belong to the candidate."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="must belong to the candidate",
    ):
        CandidateAnalysis(
            workflow_id=workflow_id,
            candidate_name="Company A",
            status=AnalysisStatus.COMPLETED,
            category_evaluations=[
                create_category_evaluation(
                    workflow_id=workflow_id,
                    candidate_name="Company B",
                )
            ],
            confidence=ConfidenceLevel.MODERATE,
            rationale="Candidate analysis.",
        )


def test_analysis_rejects_duplicate_categories() -> None:
    """Candidate category names should be unique."""

    workflow_id = uuid4()

    first_evaluation = create_category_evaluation(
        workflow_id=workflow_id,
        category_name="Profitability",
    )
    second_evaluation = create_category_evaluation(
        workflow_id=workflow_id,
        category_name="profitability",
    )

    with pytest.raises(
        ValidationError,
        match="category names must be unique",
    ):
        CandidateAnalysis(
            workflow_id=workflow_id,
            candidate_name="Company A",
            status=AnalysisStatus.COMPLETED,
            category_evaluations=[
                first_evaluation,
                second_evaluation,
            ],
            confidence=ConfidenceLevel.MODERATE,
            rationale="Candidate analysis.",
        )


def test_insufficient_analysis_rejects_weighted_score() -> None:
    """Insufficient evidence cannot produce a weighted score."""

    with pytest.raises(
        ValidationError,
        match="cannot contain a weighted score",
    ):
        CandidateAnalysis(
            workflow_id=uuid4(),
            candidate_name="Company A",
            status=AnalysisStatus.INSUFFICIENT_EVIDENCE,
            missing_information=[
                "Current financial statements"
            ],
            weighted_score=Decimal("35"),
            confidence=ConfidenceLevel.INSUFFICIENT,
            rationale="Evidence is insufficient.",
        )


def test_completed_analysis_rejects_insufficient_confidence() -> None:
    """Completed analysis cannot use insufficient confidence."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="cannot use insufficient confidence",
    ):
        CandidateAnalysis(
            workflow_id=workflow_id,
            candidate_name="Company A",
            status=AnalysisStatus.COMPLETED,
            category_evaluations=[
                create_category_evaluation(workflow_id)
            ],
            confidence=ConfidenceLevel.INSUFFICIENT,
            rationale="Candidate analysis.",
        )


def test_ranked_recommendation_accepts_preferred_candidate() -> None:
    """Ranked outcome should identify and rank a preferred candidate."""

    recommendation = RecommendationResult(
        workflow_id=uuid4(),
        outcome=RecommendationOutcome.RANKED_RECOMMENDATION,
        preferred_candidate="Company A",
        alternative_candidates=["Company B"],
        ranked_candidates=["Company A", "Company B"],
        candidate_analysis_ids=[uuid4(), uuid4()],
        supporting_evidence_ids=[uuid4()],
        opposing_evidence_ids=[uuid4()],
        material_risks=["Market conditions may change."],
        rationale=(
            "Company A is most aligned with the supplied criteria."
        ),
        confidence=ConfidenceLevel.MODERATE,
        human_review_required=True,
    )

    assert recommendation.preferred_candidate == "Company A"
    assert recommendation.ranked_candidates[0] == "Company A"
    assert recommendation.alternative_candidates == ["Company B"]
    assert recommendation.human_review_required is True


def test_ranked_recommendation_requires_preferred_candidate() -> None:
    """Ranked recommendation must identify a preferred candidate."""

    with pytest.raises(
        ValidationError,
        match="require a preferred candidate",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RANKED_RECOMMENDATION,
            ranked_candidates=["Company A", "Company B"],
            rationale="Candidate ranking.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_qualified_recommendation_requires_preferred_candidate() -> None:
    """Qualified recommendation must identify a preferred candidate."""

    with pytest.raises(
        ValidationError,
        match="require a preferred candidate",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.QUALIFIED_RECOMMENDATION,
            ranked_candidates=["Company A", "Company B"],
            rationale="Qualified candidate comparison.",
            confidence=ConfidenceLevel.LOW,
        )


def test_ranked_recommendation_requires_ranking() -> None:
    """Ranked recommendation must contain a candidate ranking."""

    with pytest.raises(
        ValidationError,
        match="requires a candidate ranking",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RANKED_RECOMMENDATION,
            preferred_candidate="Company A",
            ranked_candidates=[],
            rationale="Candidate ranking.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_insufficient_evidence_rejects_preferred_candidate() -> None:
    """Insufficient evidence cannot identify a preferred candidate."""

    with pytest.raises(
        ValidationError,
        match="cannot identify a preferred candidate",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.INSUFFICIENT_EVIDENCE,
            preferred_candidate="Company A",
            rationale="Evidence is insufficient.",
            confidence=ConfidenceLevel.INSUFFICIENT,
        )


def test_shortlist_rejects_preferred_candidate() -> None:
    """A research shortlist should not identify one preferred candidate."""

    with pytest.raises(
        ValidationError,
        match="cannot identify a preferred candidate",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RESEARCH_SHORTLIST,
            preferred_candidate="Company A",
            ranked_candidates=["Company A", "Company B"],
            rationale="The candidates require additional review.",
            confidence=ConfidenceLevel.LOW,
        )


def test_no_aligned_candidate_rejects_preferred_candidate() -> None:
    """No-aligned-candidate outcome cannot name a preferred candidate."""

    with pytest.raises(
        ValidationError,
        match="cannot identify a preferred candidate",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.NO_ALIGNED_CANDIDATE,
            preferred_candidate="Company A",
            rationale="No candidate satisfies the supplied criteria.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_preferred_candidate_must_rank_first() -> None:
    """Preferred candidate must be first in the ranking."""

    with pytest.raises(
        ValidationError,
        match="must be first in the candidate ranking",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RANKED_RECOMMENDATION,
            preferred_candidate="Company A",
            ranked_candidates=["Company B", "Company A"],
            rationale="Candidate ranking.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_recommendation_rejects_duplicate_ranked_candidates() -> None:
    """Ranked candidates should be unique regardless of case."""

    with pytest.raises(
        ValidationError,
        match="Ranked candidates must be unique",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RANKED_RECOMMENDATION,
            preferred_candidate="Company A",
            ranked_candidates=["Company A", "company a"],
            rationale="Candidate ranking.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_recommendation_rejects_duplicate_alternatives() -> None:
    """Alternative candidates should be unique regardless of case."""

    with pytest.raises(
        ValidationError,
        match="Alternative candidates must be unique",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RANKED_RECOMMENDATION,
            preferred_candidate="Company A",
            alternative_candidates=["Company B", "company b"],
            ranked_candidates=["Company A", "Company B"],
            rationale="Candidate ranking.",
            confidence=ConfidenceLevel.MODERATE,
        )


def test_recommendation_rejects_duplicate_record_references() -> None:
    """Recommendation record references should be unique."""

    analysis_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="Recommendation identifiers must be unique",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RESEARCH_SHORTLIST,
            ranked_candidates=["Company A", "Company B"],
            candidate_analysis_ids=[analysis_id, analysis_id],
            rationale="The candidates require additional review.",
            confidence=ConfidenceLevel.LOW,
        )


def test_human_review_cannot_be_disabled() -> None:
    """Every recommendation requires human review."""

    with pytest.raises(
        ValidationError,
        match="Human review must always be required",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RESEARCH_SHORTLIST,
            ranked_candidates=["Company A", "Company B"],
            rationale="The candidates require human review.",
            confidence=ConfidenceLevel.LOW,
            human_review_required=False,
        )


def test_insufficient_outcome_requires_insufficient_confidence() -> None:
    """Insufficient-evidence outcome requires matching confidence."""

    with pytest.raises(
        ValidationError,
        match="requires insufficient confidence",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.INSUFFICIENT_EVIDENCE,
            rationale="Evidence is insufficient.",
            confidence=ConfidenceLevel.LOW,
        )


def test_recommendation_rejects_naive_timestamp() -> None:
    """Recommendation timestamps must be timezone-aware."""

    with pytest.raises(
        ValidationError,
        match="created_at must be timezone-aware",
    ):
        RecommendationResult(
            workflow_id=uuid4(),
            outcome=RecommendationOutcome.RESEARCH_SHORTLIST,
            ranked_candidates=["Company A", "Company B"],
            rationale="Further human review is required.",
            confidence=ConfidenceLevel.LOW,
            created_at=datetime(2026, 9, 11, 10, 0, 0),
        )


def test_financial_models_reject_unknown_fields() -> None:
    """Financial contracts should reject undocumented fields."""

    with pytest.raises(ValidationError):
        FinancialInput(
            workflow_id=uuid4(),
            candidate_name="Company A",
            metric_name="revenue",
            value=Decimal("100"),
            reporting_period="FY2025",
            availability_status=(
                DataAvailabilityStatus.AVAILABLE
            ),
            evidence_id=uuid4(),
            undocumented_field="unexpected value",
        )


def test_financial_input_serialization_round_trip() -> None:
    """A financial input should serialize and reconstruct correctly."""

    financial_input = FinancialInput(
        workflow_id=uuid4(),
        candidate_name="Company A",
        metric_name="revenue",
        value=Decimal("2500000000"),
        currency="USD",
        unit="currency_units",
        reporting_period="FY2025",
        availability_status=DataAvailabilityStatus.AVAILABLE,
        evidence_id=uuid4(),
    )

    serialized = financial_input.model_dump_json()
    reconstructed = FinancialInput.model_validate_json(serialized)

    assert reconstructed == financial_input


def test_recommendation_serialization_round_trip() -> None:
    """A recommendation should serialize and reconstruct correctly."""

    recommendation = RecommendationResult(
        workflow_id=uuid4(),
        outcome=RecommendationOutcome.RANKED_RECOMMENDATION,
        preferred_candidate="Company A",
        alternative_candidates=["Company B"],
        ranked_candidates=["Company A", "Company B"],
        candidate_analysis_ids=[uuid4(), uuid4()],
        supporting_evidence_ids=[uuid4()],
        opposing_evidence_ids=[uuid4()],
        material_risks=["Market conditions may change."],
        rationale=(
            "Company A is most aligned with the supplied criteria."
        ),
        confidence=ConfidenceLevel.MODERATE,
        human_review_required=True,
    )

    serialized = recommendation.model_dump_json()
    reconstructed = RecommendationResult.model_validate_json(
        serialized
    )

    assert reconstructed == recommendation