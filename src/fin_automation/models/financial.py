"""Structured contracts for financial calculations and analysis."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from fin_automation.models.common import (
    AnalysisStatus,
    CalculationStatus,
    CalculationType,
    ConfidenceLevel,
    DataAvailabilityStatus,
    RecommendationOutcome,
)


class FinancialBaseModel(BaseModel):
    """Base configuration shared by financial models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class FinancialInput(FinancialBaseModel):
    """One validated financial value used by a calculation."""

    input_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    candidate_name: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    value: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    reporting_period: str = Field(min_length=1)
    availability_status: DataAvailabilityStatus
    evidence_id: UUID

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str | None,
    ) -> str | None:
        """Validate and normalize an optional currency code."""

        if value is None:
            return None

        normalized_currency = value.upper()

        if len(normalized_currency) != 3:
            raise ValueError(
                "Currency must use a three-character code."
            )

        return normalized_currency

    @model_validator(mode="after")
    def validate_financial_input(self) -> "FinancialInput":
        """Validate the relationship between availability and value."""

        if (
            self.availability_status
            == DataAvailabilityStatus.AVAILABLE
            and self.value is None
        ):
            raise ValueError(
                "Available financial input requires a numeric value."
            )

        unavailable_statuses = {
            DataAvailabilityStatus.MISSING,
            DataAvailabilityStatus.UNAVAILABLE,
            DataAvailabilityStatus.INVALID,
            DataAvailabilityStatus.INSUFFICIENT,
            DataAvailabilityStatus.NOT_APPLICABLE,
        }

        if (
            self.availability_status in unavailable_statuses
            and self.value is not None
        ):
            raise ValueError(
                "A non-available financial input cannot contain a "
                "usable numeric value."
            )

        return self
class CalculationRecord(FinancialBaseModel):
    """One deterministic financial calculation and its lineage."""

    calculation_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    candidate_name: str | None = None
    calculation_type: CalculationType
    status: CalculationStatus
    formula_name: str = Field(min_length=1)
    input_ids: list[UUID] = Field(default_factory=list)
    result: Decimal | None = None
    result_unit: str | None = None
    reporting_period: str | None = None
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("input_ids")
    @classmethod
    def validate_unique_input_ids(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate calculation-input identifiers."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Calculation input identifiers must be unique."
            )

        return values

    @field_validator("created_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        """Require a timezone-aware creation timestamp."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        return value

    @model_validator(mode="after")
    def validate_calculation_record(self) -> "CalculationRecord":
        """Validate calculation status, inputs, and results."""

        if self.status == CalculationStatus.COMPLETED:
            if self.result is None:
                raise ValueError(
                    "Completed calculation requires a numeric result."
                )

            if not self.input_ids:
                raise ValueError(
                    "Completed calculation requires at least one input."
                )

        elif self.result is not None:
            raise ValueError(
                "An incomplete calculation cannot contain a usable "
                "result."
            )

        if (
            self.calculation_type
            != CalculationType.WEIGHTED_SCORE
            and self.candidate_name is None
        ):
            raise ValueError(
                "Candidate name is required for candidate-level "
                "calculations."
            )

        return self


class CategoryEvaluation(FinancialBaseModel):
    """One methodology-category evaluation for one candidate."""

    evaluation_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    candidate_name: str = Field(min_length=1)
    category_name: str = Field(min_length=1)
    availability_status: DataAvailabilityStatus
    score: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("100"),
    )
    calculation_ids: list[UUID] = Field(default_factory=list)
    supporting_evidence_ids: list[UUID] = Field(
        default_factory=list
    )
    opposing_evidence_ids: list[UUID] = Field(
        default_factory=list
    )
    risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    confidence: ConfidenceLevel

    @field_validator(
        "calculation_ids",
        "supporting_evidence_ids",
        "opposing_evidence_ids",
    )
    @classmethod
    def validate_unique_identifiers(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate references within identifier lists."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Referenced identifiers must be unique."
            )

        return values

    @model_validator(mode="after")
    def validate_category_evaluation(
        self,
    ) -> "CategoryEvaluation":
        """Validate score and availability behavior."""

        if (
            self.availability_status
            == DataAvailabilityStatus.AVAILABLE
            and self.score is None
        ):
            raise ValueError(
                "An available category evaluation requires a score."
            )

        unavailable_statuses = {
            DataAvailabilityStatus.MISSING,
            DataAvailabilityStatus.UNAVAILABLE,
            DataAvailabilityStatus.INVALID,
            DataAvailabilityStatus.INSUFFICIENT,
            DataAvailabilityStatus.NOT_APPLICABLE,
        }

        if (
            self.availability_status in unavailable_statuses
            and self.score is not None
        ):
            raise ValueError(
                "Missing, unavailable, invalid, insufficient, or "
                "non-applicable categories cannot receive a score."
            )

        if (
            self.confidence == ConfidenceLevel.INSUFFICIENT
            and self.availability_status
            == DataAvailabilityStatus.AVAILABLE
        ):
            raise ValueError(
                "An available category cannot use insufficient "
                "confidence."
            )

        return self


class CandidateAnalysis(FinancialBaseModel):
    """Completed financial analysis for one candidate."""

    analysis_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    candidate_name: str = Field(min_length=1)
    status: AnalysisStatus
    category_evaluations: list[CategoryEvaluation] = Field(
        default_factory=list
    )
    calculation_ids: list[UUID] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    material_risks: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[UUID] = Field(
        default_factory=list
    )
    opposing_evidence_ids: list[UUID] = Field(
        default_factory=list
    )
    missing_information: list[str] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)
    weighted_score: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("100"),
    )
    confidence: ConfidenceLevel
    rationale: str = Field(min_length=1)

    @field_validator(
        "calculation_ids",
        "supporting_evidence_ids",
        "opposing_evidence_ids",
    )
    @classmethod
    def validate_unique_identifiers(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate analysis references."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Candidate-analysis identifiers must be unique."
            )

        return values

    @model_validator(mode="after")
    def validate_candidate_analysis(
        self,
    ) -> "CandidateAnalysis":
        """Validate nested evaluations and analysis status."""

        if (
            self.status == AnalysisStatus.COMPLETED
            and not self.category_evaluations
        ):
            raise ValueError(
                "Completed candidate analysis requires at least one "
                "category evaluation."
            )

        for evaluation in self.category_evaluations:
            if evaluation.workflow_id != self.workflow_id:
                raise ValueError(
                    "Category evaluations must use the same workflow_id "
                    "as CandidateAnalysis."
                )

            if (
                evaluation.candidate_name.casefold()
                != self.candidate_name.casefold()
            ):
                raise ValueError(
                    "Category evaluations must belong to the candidate "
                    "being analyzed."
                )

        category_names = [
            evaluation.category_name.casefold()
            for evaluation in self.category_evaluations
        ]

        if len(category_names) != len(set(category_names)):
            raise ValueError(
                "Candidate-analysis category names must be unique."
            )

        if (
            self.status
            == AnalysisStatus.INSUFFICIENT_EVIDENCE
            and self.weighted_score is not None
        ):
            raise ValueError(
                "Insufficient-evidence analysis cannot contain a "
                "weighted score."
            )

        if (
            self.confidence == ConfidenceLevel.INSUFFICIENT
            and self.status == AnalysisStatus.COMPLETED
        ):
            raise ValueError(
                "Completed analysis cannot use insufficient confidence."
            )

        return self


class RecommendationResult(FinancialBaseModel):
    """The preliminary financial research conclusion."""

    recommendation_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    outcome: RecommendationOutcome
    preferred_candidate: str | None = None
    alternative_candidates: list[str] = Field(default_factory=list)
    ranked_candidates: list[str] = Field(default_factory=list)
    candidate_analysis_ids: list[UUID] = Field(
        default_factory=list
    )
    supporting_evidence_ids: list[UUID] = Field(
        default_factory=list
    )
    opposing_evidence_ids: list[UUID] = Field(
        default_factory=list
    )
    material_risks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    confidence: ConfidenceLevel
    human_review_required: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "candidate_analysis_ids",
        "supporting_evidence_ids",
        "opposing_evidence_ids",
    )
    @classmethod
    def validate_unique_identifiers(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate recommendation references."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Recommendation identifiers must be unique."
            )

        return values

    @field_validator("created_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        """Require a timezone-aware creation timestamp."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        return value

    @model_validator(mode="after")
    def validate_recommendation_result(
        self,
    ) -> "RecommendationResult":
        """Validate outcome, candidate, and human-review behavior."""

        preferred_candidate_outcomes = {
            RecommendationOutcome.RANKED_RECOMMENDATION,
            RecommendationOutcome.QUALIFIED_RECOMMENDATION,
        }

        if (
            self.outcome in preferred_candidate_outcomes
            and not self.preferred_candidate
        ):
            raise ValueError(
                "Ranked and qualified recommendations require a "
                "preferred candidate."
            )

        no_preferred_candidate_outcomes = {
            RecommendationOutcome.RESEARCH_SHORTLIST,
            RecommendationOutcome.NO_ALIGNED_CANDIDATE,
            RecommendationOutcome.INSUFFICIENT_EVIDENCE,
        }

        if (
            self.outcome in no_preferred_candidate_outcomes
            and self.preferred_candidate is not None
        ):
            raise ValueError(
                "This recommendation outcome cannot identify a "
                "preferred candidate."
            )

        normalized_ranked_candidates = [
            candidate.casefold()
            for candidate in self.ranked_candidates
        ]

        if len(normalized_ranked_candidates) != len(
            set(normalized_ranked_candidates)
        ):
            raise ValueError(
                "Ranked candidates must be unique."
            )

        normalized_alternatives = [
            candidate.casefold()
            for candidate in self.alternative_candidates
        ]

        if len(normalized_alternatives) != len(
            set(normalized_alternatives)
        ):
            raise ValueError(
                "Alternative candidates must be unique."
            )

        if (
            self.preferred_candidate is not None
            and self.ranked_candidates
            and self.ranked_candidates[0].casefold()
            != self.preferred_candidate.casefold()
        ):
            raise ValueError(
                "The preferred candidate must be first in the "
                "candidate ranking."
            )

        if (
            self.outcome
            == RecommendationOutcome.RANKED_RECOMMENDATION
            and not self.ranked_candidates
        ):
            raise ValueError(
                "A ranked recommendation requires a candidate ranking."
            )

        if not self.human_review_required:
            raise ValueError(
                "Human review must always be required."
            )

        if (
            self.outcome
            == RecommendationOutcome.INSUFFICIENT_EVIDENCE
            and self.confidence != ConfidenceLevel.INSUFFICIENT
        ):
            raise ValueError(
                "An insufficient-evidence outcome requires "
                "insufficient confidence."
            )

        return self