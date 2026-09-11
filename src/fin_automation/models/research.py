"""Structured models for financial research planning."""

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
    SearchPurpose,
    SourceCategory,
    WorkflowStage,
)


class ResearchBaseModel(BaseModel):
    """Base configuration shared by research-planning models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class EvidenceRequirement(ResearchBaseModel):
    """A category of evidence required by the research plan."""

    requirement_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    candidate_name: str | None = None
    search_purpose: SearchPurpose
    preferred_source_categories: list[SourceCategory] = Field(
        min_length=1
    )
    required: bool = True


class SearchQuery(ResearchBaseModel):
    """One approved query that may be executed by the web-search tool."""

    query_id: UUID = Field(default_factory=uuid4)
    query: str = Field(min_length=1)
    purpose: SearchPurpose
    candidate_name: str | None = None
    evidence_requirement_ids: list[UUID] = Field(min_length=1)

    @field_validator("evidence_requirement_ids")
    @classmethod
    def validate_unique_evidence_requirement_ids(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate evidence-requirement references."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Search-query evidence_requirement_ids "
                "must be unique."
            )

        return values


class AdditionalResearchRequest(ResearchBaseModel):
    """A bounded request for another research pass."""

    request_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    requested_by_stage: WorkflowStage
    candidate_name: str | None = None
    missing_evidence: str = Field(min_length=1)
    evidence_requirement_id: UUID | None = None
    reason: str = Field(min_length=1)
    suggested_search_purpose: SearchPurpose
    blocks_recommendation: bool = False
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


class ResearchPlan(ResearchBaseModel):
    """The approved plan governing candidate research."""

    plan_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    research_objective: str = Field(min_length=1)
    candidate_discovery_required: bool
    candidate_names: list[str] = Field(default_factory=list)
    comparison_criteria: list[str] = Field(min_length=1)
    risk_categories: list[str] = Field(default_factory=list)
    evidence_requirements: list[EvidenceRequirement] = Field(
        min_length=1
    )
    search_queries: list[SearchQuery] = Field(min_length=1)
    preferred_source_categories: list[SourceCategory] = Field(
        min_length=1
    )
    candidate_limit: int = Field(default=3, ge=1, le=3)
    source_limit_per_candidate: int = Field(
        default=5,
        ge=1,
        le=10,
    )
    assumptions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @model_validator(mode="after")
    def validate_research_plan(self) -> "ResearchPlan":
        """Validate identifiers, references, and candidate behavior."""

        requirement_ids = [
            requirement.requirement_id
            for requirement in self.evidence_requirements
        ]

        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError(
                "Evidence-requirement identifiers must be unique."
            )

        query_ids = [
            search_query.query_id
            for search_query in self.search_queries
        ]

        if len(query_ids) != len(set(query_ids)):
            raise ValueError(
                "Search-query identifiers must be unique."
            )

        known_requirement_ids = set(requirement_ids)

        for search_query in self.search_queries:
            unknown_requirement_ids = (
                set(search_query.evidence_requirement_ids)
                - known_requirement_ids
            )

            if unknown_requirement_ids:
                raise ValueError(
                    "Every search-query evidence reference must "
                    "resolve to an evidence requirement in the plan."
                )

        normalized_candidate_names = [
            candidate.casefold()
            for candidate in self.candidate_names
        ]

        if len(normalized_candidate_names) != len(
            set(normalized_candidate_names)
        ):
            raise ValueError(
                "Candidate names must be unique."
            )

        if len(self.candidate_names) > self.candidate_limit:
            raise ValueError(
                "The number of candidate names cannot exceed "
                "candidate_limit."
            )

        if (
            not self.candidate_discovery_required
            and not self.candidate_names
        ):
            raise ValueError(
                "candidate_names are required when candidate "
                "discovery is not required."
            )

        preferred_categories = set(
            self.preferred_source_categories
        )

        if SourceCategory.UNSUPPORTED in preferred_categories:
            raise ValueError(
                "Unsupported sources cannot be preferred."
            )

        requirement_map = {
            requirement.requirement_id: requirement
            for requirement in self.evidence_requirements
        }

        for search_query in self.search_queries:
            referenced_purposes = {
                requirement_map[
                    requirement_id
                ].search_purpose
                for requirement_id
                in search_query.evidence_requirement_ids
            }

            if search_query.purpose not in referenced_purposes:
                raise ValueError(
                    "Each search query must reference at least one "
                    "evidence requirement with the same purpose."
                )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware."
            )

        return self