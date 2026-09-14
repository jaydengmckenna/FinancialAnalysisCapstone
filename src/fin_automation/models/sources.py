"""Structured contracts for search, retrieval, sources, and evidence."""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    AnyHttpUrl,
    field_validator,
    model_validator,
)

from fin_automation.models.common import (
    ParsingStatus,
    RetrievalStatus,
    SourceCategory,
    SourceSelectionStatus,
)
from fin_automation.models.research import AdditionalResearchRequest


class SourceBaseModel(BaseModel):
    """Base configuration shared by source and evidence models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class SearchResult(SourceBaseModel):
    """Validated search result returned by Tavily."""

    search_result_id: UUID = Field(
        default_factory=uuid4,
    )

    workflow_id: UUID

    query_id: UUID

    title: str = Field(
        min_length=1,
    )

    url: AnyHttpUrl

    snippet: str | None = None

    raw_content: str | None = None

    domain: str = Field(
        min_length=1,
    )

    result_position: int = Field(
        ge=1,
    )

    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @field_validator("retrieved_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        """Require a timezone-aware retrieval timestamp."""

        if value.tzinfo is None:
            raise ValueError(
                "retrieved_at must be timezone-aware."
            )

        return value
class SelectedSource(SourceBaseModel):
    """Search result reviewed by the Source Selection Agent."""

    selection_id: UUID = Field(
        default_factory=uuid4,
    )

    search_result_id: UUID

    url: AnyHttpUrl

    title: str = Field(
        min_length=1,
    )

    domain: str = Field(
        min_length=1,
    )

    raw_content: str | None = None

    candidate_name: str | None = None

    selected: bool

    expected_source_category: SourceCategory

    selection_reason: str = Field(
        min_length=1,
    )

    exclusion_reason: str | None = None

    evidence_requirement_ids: list[UUID] = Field(
        default_factory=list,
    )

    @field_validator("evidence_requirement_ids")
    @classmethod
    def validate_unique_evidence_requirement_ids(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate evidence-requirement references."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Selected-source evidence_requirement_ids "
                "must be unique."
            )

        return values

    @model_validator(mode="after")
    def validate_selection_decision(self) -> "SelectedSource":
        """Validate selected and excluded source behavior."""

        if self.selected and not self.evidence_requirement_ids:
            raise ValueError(
                "A selected source must reference at least one "
                "evidence requirement."
            )

        if self.selected and self.exclusion_reason is not None:
            raise ValueError(
                "A selected source cannot have an exclusion reason."
            )

        if not self.selected and not self.exclusion_reason:
            raise ValueError(
                "An excluded source must include an exclusion reason."
            )

        if (
            self.selected
            and self.expected_source_category
            == SourceCategory.UNSUPPORTED
        ):
            raise ValueError(
                "An unsupported source cannot be selected for retrieval."
            )

        return self


class SourceSelection(SourceBaseModel):
    """The complete source-selection result for one research pass."""

    source_selection_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    plan_id: UUID
    status: SourceSelectionStatus
    selections: list[SelectedSource] = Field(default_factory=list)
    uncovered_evidence_requirement_ids: list[UUID] = Field(
        default_factory=list
    )
    additional_research_requests: list[
        AdditionalResearchRequest
    ] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("uncovered_evidence_requirement_ids")
    @classmethod
    def validate_unique_uncovered_requirement_ids(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate uncovered evidence requirements."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Uncovered evidence-requirement identifiers "
                "must be unique."
            )

        return values

    @model_validator(mode="after")
    def validate_source_selection(self) -> "SourceSelection":
        """Validate status and nested source-selection records."""

        search_result_ids = [
            selection.search_result_id
            for selection in self.selections
        ]

        if len(search_result_ids) != len(set(search_result_ids)):
            raise ValueError(
                "Each search result may appear only once in "
                "SourceSelection."
            )

        selected_sources = [
            selection
            for selection in self.selections
            if selection.selected
        ]

        if (
            self.status
            == SourceSelectionStatus.READY_FOR_RETRIEVAL
            and not selected_sources
        ):
            raise ValueError(
                "ready_for_retrieval requires at least one "
                "selected source."
            )

        if (
            self.status
            == SourceSelectionStatus.ADDITIONAL_SEARCH_REQUIRED
            and not self.additional_research_requests
        ):
            raise ValueError(
                "additional_search_required requires at least one "
                "additional research request."
            )

        for request in self.additional_research_requests:
            if request.workflow_id != self.workflow_id:
                raise ValueError(
                    "Additional research requests must use the same "
                    "workflow_id as SourceSelection."
                )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware."
            )

        return self


class RetrievalResult(SourceBaseModel):
    """The result of retrieving one selected webpage."""

    retrieval_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    search_result_id: UUID
    requested_url: AnyHttpUrl
    final_url: AnyHttpUrl | None = None
    status: RetrievalStatus
    http_status_code: int | None = Field(
        default=None,
        ge=100,
        le=599,
    )
    content_type: str | None = None
    retrieved_at: datetime | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def validate_retrieval_result(self) -> "RetrievalResult":
        """Validate successful and unsuccessful retrieval outcomes."""

        if self.status == RetrievalStatus.SUCCESS:
            if self.final_url is None:
                raise ValueError(
                    "Successful retrieval requires a final URL."
                )

            if self.retrieved_at is None:
                raise ValueError(
                    "Successful retrieval requires a retrieval timestamp."
                )

            if self.error_message is not None:
                raise ValueError(
                    "Successful retrieval cannot contain an error message."
                )

        elif not self.error_message:
            raise ValueError(
                "Unsuccessful retrieval requires an error message."
            )

        if self.retrieved_at is not None:
            if (
                self.retrieved_at.tzinfo is None
                or self.retrieved_at.utcoffset() is None
            ):
                raise ValueError(
                    "retrieved_at must be timezone-aware."
                )

        return self


class SourceRecord(SourceBaseModel):
    """A retrieved and parsed public source."""

    source_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    retrieval_id: UUID
    search_result_id: UUID
    title: str = Field(min_length=1)
    url: AnyHttpUrl
    publisher: str | None = None
    author: str | None = None
    publication_date: date | None = None
    retrieval_date: date
    source_category: SourceCategory
    parsing_status: ParsingStatus
    candidate_names: list[str] = Field(default_factory=list)
    evidence_requirement_ids: list[UUID] = Field(
        default_factory=list
    )
    content_summary: str | None = None
    limitations: list[str] = Field(default_factory=list)

    @field_validator("evidence_requirement_ids")
    @classmethod
    def validate_unique_evidence_requirement_ids(
        cls,
        values: list[UUID],
    ) -> list:
        """Reject duplicate evidence-requirement references."""

        if len(values) != len(set(values)):
            raise ValueError(
                "Source-record evidence_requirement_ids "
                "must be unique."
            )

        return values

    @model_validator(mode="after")
    def validate_source_record(self) -> "SourceRecord":
        """Validate source metadata and parsing outcomes."""

        normalized_candidate_names = [
            candidate.casefold()
            for candidate in self.candidate_names
        ]

        if len(normalized_candidate_names) != len(
            set(normalized_candidate_names)
        ):
            raise ValueError(
                "Source-record candidate names must be unique."
            )

        if (
            self.parsing_status == ParsingStatus.SUCCESS
            and not self.content_summary
        ):
            raise ValueError(
                "Successful parsing requires a content summary."
            )

        if (
            self.parsing_status == ParsingStatus.NOT_ATTEMPTED
            and self.content_summary is not None
        ):
            raise ValueError(
                "A source that was not parsed cannot have a "
                "content summary."
            )

        return self


class ExtractedEvidence(SourceBaseModel):
    """One factual passage or value extracted from a source."""

    evidence_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    source_id: UUID
    candidate_name: str | None = None
    evidence_requirement_id: UUID | None = None
    evidence_type: str = Field(min_length=1)
    content: str = Field(min_length=1)
    section_heading: str | None = None
    reported_value: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    reporting_period: str | None = None
    supports_candidate: bool | None = None
    extraction_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_numeric_evidence(self) -> "ExtractedEvidence":
        """Validate metadata associated with numeric evidence."""

        numeric_metadata_present = any(
            value is not None
            for value in (
                self.currency,
                self.unit,
                self.reporting_period,
            )
        )

        if self.reported_value is None and numeric_metadata_present:
            raise ValueError(
                "Currency, unit, and reporting period require a "
                "reported numeric value."
            )

        return self