"""Structured models for interpreting a user's research request."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from fin_automation.models.common import (
    AssetType,
    InvestmentObjective,
    RequestType,
    RiskTolerance,
    TimeHorizon,
)


class IntakeBaseModel(BaseModel):
    """Base configuration shared by intake models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ResearchRequest(IntakeBaseModel):
    """Structured representation of the user's research question."""

    request_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    original_prompt: str = Field(min_length=1)
    research_question: str = Field(min_length=1)
    request_type: RequestType
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("created_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        """Require a timezone-aware creation timestamp."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware.")

        return value


class InvestorProfile(IntakeBaseModel):
    """Investor preferences explicitly stated or confirmed by the user."""

    profile_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    risk_tolerance: RiskTolerance | None = None
    investment_objective: InvestmentObjective | None = None
    time_horizon: TimeHorizon | None = None
    growth_or_income_preference: str | None = None
    geographic_preferences: list[str] = Field(default_factory=list)
    industry_preferences: list[str] = Field(default_factory=list)
    excluded_regions: list[str] = Field(default_factory=list)
    excluded_industries: list[str] = Field(default_factory=list)
    explicit_constraints: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_preferences_and_exclusions(
        self,
    ) -> "InvestorProfile":
        """Prevent the same preference from also being excluded."""

        geographic_preferences = {
            value.casefold()
            for value in self.geographic_preferences
        }
        excluded_regions = {
            value.casefold()
            for value in self.excluded_regions
        }

        overlapping_regions = (
            geographic_preferences & excluded_regions
        )

        if overlapping_regions:
            raise ValueError(
                "Geographic preferences and excluded regions "
                "must not overlap."
            )

        industry_preferences = {
            value.casefold()
            for value in self.industry_preferences
        }
        excluded_industries = {
            value.casefold()
            for value in self.excluded_industries
        }

        overlapping_industries = (
            industry_preferences & excluded_industries
        )

        if overlapping_industries:
            raise ValueError(
                "Industry preferences and excluded industries "
                "must not overlap."
            )

        return self


class ResearchScope(IntakeBaseModel):
    """Boundaries of the requested investment research."""

    scope_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    asset_types: list[AssetType] = Field(
        default_factory=lambda: [AssetType.PUBLIC_STOCK],
        min_length=1,
    )
    named_candidates: list[str] = Field(default_factory=list)
    candidate_limit: int = Field(default=3, ge=1, le=3)
    geographic_scope: list[str] = Field(default_factory=list)
    industry_scope: list[str] = Field(default_factory=list)
    excluded_candidates: list[str] = Field(default_factory=list)
    additional_constraints: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_candidate_lists(
        self,
    ) -> "ResearchScope":
        """Prevent candidates from being both included and excluded."""

        named_candidates = {
            candidate.casefold()
            for candidate in self.named_candidates
        }
        excluded_candidates = {
            candidate.casefold()
            for candidate in self.excluded_candidates
        }

        overlapping_candidates = (
            named_candidates & excluded_candidates
        )

        if overlapping_candidates:
            raise ValueError(
                "Named candidates and excluded candidates "
                "must not overlap."
            )

        if len(named_candidates) > self.candidate_limit:
            raise ValueError(
                "The number of named candidates cannot exceed "
                "candidate_limit."
            )

        return self


class IntakeResult(IntakeBaseModel):
    """Validated result of natural-language request interpretation."""

    intake_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    research_request: ResearchRequest
    investor_profile: InvestorProfile
    research_scope: ResearchScope
    assumptions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_questions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @model_validator(mode="after")
    def validate_intake_result(self) -> "IntakeResult":
        """Validate workflow identity and clarification consistency."""

        nested_workflow_ids = {
            self.research_request.workflow_id,
            self.investor_profile.workflow_id,
            self.research_scope.workflow_id,
        }

        if nested_workflow_ids != {self.workflow_id}:
            raise ValueError(
                "All intake records must use the same workflow_id."
            )

        required_profile_fields = {
            "risk_tolerance": self.investor_profile.risk_tolerance,
            "investment_objective": (
                self.investor_profile.investment_objective
            ),
            "time_horizon": self.investor_profile.time_horizon,
        }

        actually_missing = {
            field_name
            for field_name, value in required_profile_fields.items()
            if value is None
        }

        declared_missing = set(self.missing_fields)

        if declared_missing != actually_missing:
            raise ValueError(
                "missing_fields must exactly identify the missing required "
                "investor-profile fields."
            )

        if actually_missing and not self.requires_clarification:
            raise ValueError(
                "requires_clarification must be true when required "
                "investor-profile fields are missing."
            )

        if self.requires_clarification:
            if not self.missing_fields:
                raise ValueError(
                    "Clarification requires at least one missing field."
                )

            if not self.clarification_questions:
                raise ValueError(
                    "Clarification requires at least one question."
                )

        if (
            not self.requires_clarification
            and self.clarification_questions
        ):
            raise ValueError(
                "Clarification questions must be empty when "
                "clarification is not required."
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware."
            )

        return self