"""Structured contracts for reports and generated artifacts."""

from datetime import datetime, timezone
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from fin_automation.models.common import (
    ArtifactStatus,
    ArtifactType,
    RecommendationOutcome,
    ReportType,
)


class ReportBaseModel(BaseModel):
    """Base configuration shared by report models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


def validate_relative_output_path(path_value: str) -> str:
    """Validate that an artifact path remains relative and safe."""

    path = PurePosixPath(path_value)

    if path.is_absolute():
        raise ValueError(
            "Artifact paths must be relative to the output directory."
        )

    if ".." in path.parts:
        raise ValueError(
            "Artifact paths cannot escape the output directory."
        )

    if path_value in {"", "."}:
        raise ValueError(
            "Artifact paths must identify an output file."
        )

    return path_value


class ReportDraft(ReportBaseModel):
    """A validated report produced by the Report Writing Agent."""

    report_draft_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    validation_id: UUID
    recommendation_id: UUID
    report_type: ReportType
    recommendation_outcome: RecommendationOutcome
    preferred_candidate: str | None = None
    title: str = Field(min_length=1)
    markdown_content: str = Field(min_length=1)
    risks: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    human_review_statement: str = Field(min_length=1)
    candidate_analysis_ids: list[UUID] = Field(
        default_factory=list
    )
    source_ids: list[UUID] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    calculation_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "candidate_analysis_ids",
        "source_ids",
        "evidence_ids",
        "calculation_ids",
    )
    @classmethod
    def validate_unique_identifiers(
        cls,
        identifiers: list[UUID],
    ) -> list:
        """Reject duplicate references within identifier lists."""

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Report reference identifiers must be unique."
            )

        return identifiers

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
    def validate_report_draft(self) -> "ReportDraft":
        """Validate report type and recommendation consistency."""

        insufficient_outcome = (
            self.recommendation_outcome
            == RecommendationOutcome.INSUFFICIENT_EVIDENCE
        )

        if insufficient_outcome:
            if (
                self.report_type
                != ReportType.INSUFFICIENT_EVIDENCE_REPORT
            ):
                raise ValueError(
                    "An insufficient-evidence outcome requires an "
                    "insufficient-evidence report."
                )

            if self.preferred_candidate is not None:
                raise ValueError(
                    "An insufficient-evidence report cannot identify "
                    "a preferred candidate."
                )

        if (
            self.report_type
            == ReportType.INSUFFICIENT_EVIDENCE_REPORT
            and not insufficient_outcome
        ):
            raise ValueError(
                "An insufficient-evidence report requires an "
                "insufficient-evidence recommendation outcome."
            )

        preferred_candidate_outcomes = {
            RecommendationOutcome.RANKED_RECOMMENDATION,
            RecommendationOutcome.QUALIFIED_RECOMMENDATION,
        }

        if (
            self.recommendation_outcome
            in preferred_candidate_outcomes
            and not self.preferred_candidate
        ):
            raise ValueError(
                "Ranked and qualified reports require a preferred "
                "candidate."
            )

        normalized_statement = (
            self.human_review_statement.casefold()
        )

        if "human review" not in normalized_statement:
            raise ValueError(
                "The report must include an explicit human-review "
                "statement."
            )

        return self


class ReportArtifact(ReportBaseModel):
    """Metadata for one generated output file."""

    artifact_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    report_draft_id: UUID
    artifact_type: ArtifactType
    status: ArtifactStatus
    file_name: str = Field(min_length=1)
    relative_path: str | None = None
    checksum_sha256: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None

    @field_validator("relative_path")
    @classmethod
    def validate_output_path(
        cls,
        path_value: str | None,
    ) -> str | None:
        """Require output paths to remain inside the output folder."""

        if path_value is None:
            return None

        return validate_relative_output_path(path_value)

    @field_validator("created_at")
    @classmethod
    def validate_optional_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require timezone information when a timestamp is present."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        return value

    @model_validator(mode="after")
    def validate_report_artifact(self) -> "ReportArtifact":
        """Validate artifact status, path, extension, and errors."""

        expected_suffixes = {
            ArtifactType.MARKDOWN_REPORT: ".md",
            ArtifactType.JSON_WORKFLOW: ".json",
        }

        expected_suffix = expected_suffixes[self.artifact_type]

        if not self.file_name.casefold().endswith(expected_suffix):
            raise ValueError(
                f"{self.artifact_type.value} files must use the "
                f"{expected_suffix} extension."
            )

        if self.relative_path is not None:
            path = PurePosixPath(self.relative_path)

            if path.name != self.file_name:
                raise ValueError(
                    "The artifact file name must match the final "
                    "component of relative_path."
                )

        if self.status == ArtifactStatus.CREATED:
            if self.relative_path is None:
                raise ValueError(
                    "A created artifact requires a relative path."
                )

            if self.created_at is None:
                raise ValueError(
                    "A created artifact requires a creation timestamp."
                )

            if self.error_message is not None:
                raise ValueError(
                    "A created artifact cannot contain an error message."
                )

        elif self.status == ArtifactStatus.FAILED:
            if not self.error_message:
                raise ValueError(
                    "A failed artifact requires an error message."
                )

            if self.relative_path is not None:
                raise ValueError(
                    "A failed artifact cannot contain an output path."
                )

        elif self.status == ArtifactStatus.PENDING:
            if self.relative_path is not None:
                raise ValueError(
                    "A pending artifact cannot contain an output path."
                )

            if self.created_at is not None:
                raise ValueError(
                    "A pending artifact cannot have a creation timestamp."
                )

            if self.error_message is not None:
                raise ValueError(
                    "A pending artifact cannot contain an error message."
                )

        return self


class WorkflowArtifact(ReportBaseModel):
    """A bundle containing the final workflow output artifacts."""

    workflow_artifact_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    report_draft_id: UUID
    recommendation_id: UUID
    validation_id: UUID
    status: ArtifactStatus
    artifacts: list[ReportArtifact] = Field(
        default_factory=list
    )
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
            raise ValueError(
                "created_at must be timezone-aware."
            )

        return value

    @model_validator(mode="after")
    def validate_workflow_artifact(self) -> "WorkflowArtifact":
        """Validate nested artifacts and workflow completion."""

        artifact_ids = [
            artifact.artifact_id
            for artifact in self.artifacts
        ]

        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError(
                "Workflow artifact identifiers must be unique."
            )

        for artifact in self.artifacts:
            if artifact.workflow_id != self.workflow_id:
                raise ValueError(
                    "Report artifacts must use the same workflow_id "
                    "as WorkflowArtifact."
                )

            if artifact.report_draft_id != self.report_draft_id:
                raise ValueError(
                    "Report artifacts must reference the same "
                    "report_draft_id as WorkflowArtifact."
                )

        if self.status == ArtifactStatus.CREATED:
            if not self.artifacts:
                raise ValueError(
                    "A created workflow artifact requires output files."
                )

            if any(
                artifact.status != ArtifactStatus.CREATED
                for artifact in self.artifacts
            ):
                raise ValueError(
                    "A created workflow artifact may contain only "
                    "created output files."
                )

            artifact_types = {
                artifact.artifact_type
                for artifact in self.artifacts
            }

            required_types = {
                ArtifactType.MARKDOWN_REPORT,
                ArtifactType.JSON_WORKFLOW,
            }

            if not required_types.issubset(artifact_types):
                raise ValueError(
                    "A created workflow artifact requires both "
                    "Markdown and JSON output files."
                )

        elif self.status == ArtifactStatus.FAILED:
            if not any(
                artifact.status == ArtifactStatus.FAILED
                for artifact in self.artifacts
            ):
                raise ValueError(
                    "A failed workflow artifact requires at least one "
                    "failed output artifact."
                )

        elif self.status == ArtifactStatus.PENDING:
            if any(
                artifact.status != ArtifactStatus.PENDING
                for artifact in self.artifacts
            ):
                raise ValueError(
                    "A pending workflow artifact may contain only "
                    "pending output artifacts."
                )

        return self