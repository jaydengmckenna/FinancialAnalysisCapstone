"""Structured contracts for evidence validation outcomes."""

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
    CorrectionTarget,
    ValidationCategory,
    ValidationOutcome,
    ValidationSeverity,
)
from fin_automation.models.research import (
    AdditionalResearchRequest,
)


class ValidationBaseModel(BaseModel):
    """Base configuration shared by validation models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ValidationFinding(ValidationBaseModel):
    """One issue discovered during evidence validation."""

    finding_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    category: ValidationCategory
    severity: ValidationSeverity
    candidate_name: str | None = None
    affected_claim: str | None = None
    affected_calculation_id: UUID | None = None
    source_ids: list[UUID] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    description: str = Field(min_length=1)
    required_correction: str | None = None
    correction_target: CorrectionTarget

    @field_validator(
        "source_ids",
        "evidence_ids",
    )
    @classmethod
    def validate_unique_identifiers(
        cls,
        identifiers: list[UUID],
    ) -> list:
        """Reject duplicate identifiers within reference lists."""

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Validation-finding identifiers must be unique."
            )

        return identifiers

    @model_validator(mode="after")
    def validate_finding(self) -> "ValidationFinding":
        """Validate severity and correction behavior."""

        if (
            self.severity == ValidationSeverity.BLOCKING
            and not self.required_correction
        ):
            raise ValueError(
                "A blocking finding requires a correction or "
                "workflow-stopping explanation."
            )

        if (
            self.category
            == ValidationCategory.UNSUPPORTED_CLAIM
            and not self.affected_claim
        ):
            raise ValueError(
                "An unsupported-claim finding must identify the "
                "affected claim."
            )

        if (
            self.category
            == ValidationCategory.CALCULATION_INPUT_PROBLEM
            and self.affected_calculation_id is None
        ):
            raise ValueError(
                "A calculation-input finding must identify the "
                "affected calculation."
            )

        citation_categories = {
            ValidationCategory.INVALID_CITATION,
            ValidationCategory.IRRELEVANT_CITATION,
        }

        if (
            self.category in citation_categories
            and not self.source_ids
            and not self.evidence_ids
        ):
            raise ValueError(
                "A citation finding must reference at least one "
                "source or evidence record."
            )

        return self


class ValidationResult(ValidationBaseModel):
    """The Evidence Validation Agent's decision."""

    validation_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    recommendation_id: UUID
    outcome: ValidationOutcome
    findings: list[ValidationFinding] = Field(
        default_factory=list
    )
    approved_candidate_analysis_ids: list[UUID] = Field(
        default_factory=list
    )
    approved_source_ids: list[UUID] = Field(
        default_factory=list
    )
    approved_evidence_ids: list[UUID] = Field(
        default_factory=list
    )
    approved_calculation_ids: list[UUID] = Field(
        default_factory=list
    )
    additional_research_requests: list[
        AdditionalResearchRequest
    ] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "approved_candidate_analysis_ids",
        "approved_source_ids",
        "approved_evidence_ids",
        "approved_calculation_ids",
    )
    @classmethod
    def validate_unique_approved_identifiers(
        cls,
        identifiers: list[UUID],
    ) -> list:
        """Reject duplicate approved-record identifiers."""

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Approved record identifiers must be unique."
            )

        return identifiers

    @field_validator("validated_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        """Require a timezone-aware validation timestamp."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "validated_at must be timezone-aware."
            )

        return value

    @model_validator(mode="after")
    def validate_result(self) -> "ValidationResult":
        """Validate outcome, findings, and research requests."""

        for finding in self.findings:
            if finding.workflow_id != self.workflow_id:
                raise ValueError(
                    "Validation findings must use the same "
                    "workflow_id as ValidationResult."
                )

        finding_ids = [
            finding.finding_id
            for finding in self.findings
        ]

        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError(
                "Validation-finding identifiers must be unique "
                "within ValidationResult."
            )

        blocking_findings = [
            finding
            for finding in self.findings
            if finding.severity == ValidationSeverity.BLOCKING
        ]

        if (
            self.outcome == ValidationOutcome.APPROVED
            and blocking_findings
        ):
            raise ValueError(
                "An approved validation result cannot contain "
                "blocking findings."
            )

        if (
            self.outcome
            == ValidationOutcome.ANALYSIS_CORRECTION_REQUIRED
            and not self.findings
        ):
            raise ValueError(
                "Analysis correction requires at least one "
                "validation finding."
            )

        if (
            self.outcome
            == ValidationOutcome.ADDITIONAL_RESEARCH_REQUIRED
            and not self.additional_research_requests
        ):
            raise ValueError(
                "Additional-research outcome requires at least one "
                "additional research request."
            )

        if (
            self.outcome == ValidationOutcome.REJECTED
            and not blocking_findings
        ):
            raise ValueError(
                "A rejected validation result requires at least one "
                "blocking finding."
            )

        for request in self.additional_research_requests:
            if request.workflow_id != self.workflow_id:
                raise ValueError(
                    "Additional research requests must use the same "
                    "workflow_id as ValidationResult."
                )

        return self