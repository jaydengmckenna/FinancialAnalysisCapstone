"""Structured contracts for deterministic workflow state."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fin_automation.models.common import (
    ErrorSeverity,
    StageStatus,
    WorkflowStage,
    WorkflowStatus,
)


class WorkflowBaseModel(BaseModel):
    """Base configuration shared by workflow models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class WorkflowError(WorkflowBaseModel):
    """One structured error produced during workflow execution."""

    error_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    stage: WorkflowStage
    severity: ErrorSeverity
    error_type: str = Field(min_length=1)
    message: str = Field(min_length=1)
    recoverable: bool
    retry_allowed: bool = False
    retry_count: int = Field(default=0, ge=0)
    record_id: UUID | None = None
    details: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("created_at")
    @classmethod
    def validate_timezone_aware_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        """Require a timezone-aware error timestamp."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware.")

        return value

    @model_validator(mode="after")
    def validate_workflow_error(self) -> "WorkflowError":
        """Validate retry and recoverability behavior."""

        if self.retry_allowed and not self.recoverable:
            raise ValueError(
                "A nonrecoverable error cannot allow retry."
            )

        if self.retry_count > 0 and not self.retry_allowed:
            raise ValueError(
                "A positive retry count requires retry_allowed."
            )

        if (
            self.severity == ErrorSeverity.CRITICAL
            and self.recoverable
        ):
            raise ValueError(
                "A critical workflow error cannot be recoverable."
            )

        return self


class StageResult(WorkflowBaseModel):
    """Execution result and produced records for one workflow stage."""

    stage_result_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    stage: WorkflowStage
    status: StageStatus
    attempt_number: int = Field(default=1, ge=1)
    started_at: datetime
    completed_at: datetime | None = None
    produced_record_ids: list[UUID] = Field(default_factory=list)
    errors: list[WorkflowError] = Field(default_factory=list)
    summary: str | None = None

    @field_validator("started_at", "completed_at")
    @classmethod
    def validate_timezone_aware_timestamps(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require timezone information for stage timestamps."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Stage timestamps must be timezone-aware."
            )

        return value

    @field_validator("produced_record_ids")
    @classmethod
    def validate_unique_record_ids(
        cls,
        identifiers: list[UUID],
    ) -> list[UUID]:
        """Reject duplicate produced-record identifiers."""

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Produced record identifiers must be unique."
            )

        return identifiers

    @model_validator(mode="after")
    def validate_stage_result(self) -> "StageResult":
        """Validate status, timestamps, errors, and nested records."""

        terminal_statuses = {
            StageStatus.COMPLETED,
            StageStatus.FAILED,
            StageStatus.SKIPPED,
        }
        nonterminal_statuses = {
            StageStatus.NOT_STARTED,
            StageStatus.IN_PROGRESS,
            StageStatus.WAITING,
        }

        if self.status in terminal_statuses and self.completed_at is None:
            raise ValueError(
                "A terminal stage requires a completion timestamp."
            )

        if self.status in nonterminal_statuses and self.completed_at is not None:
            raise ValueError(
                "A nonterminal stage cannot have a completion timestamp."
            )

        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError(
                "Stage completion time cannot precede start time."
            )

        if self.status == StageStatus.FAILED and not self.errors:
            raise ValueError(
                "A failed stage requires at least one workflow error."
            )

        if self.status in {StageStatus.COMPLETED, StageStatus.SKIPPED} and self.errors:
            raise ValueError(
                "A successful or skipped stage cannot contain workflow errors."
            )

        error_ids = [error.error_id for error in self.errors]
        if len(error_ids) != len(set(error_ids)):
            raise ValueError(
                "Workflow-error identifiers must be unique within a stage result."
            )

        for error in self.errors:
            if error.workflow_id != self.workflow_id:
                raise ValueError(
                    "Workflow errors must use the same workflow_id as StageResult."
                )
            if error.stage != self.stage:
                raise ValueError(
                    "Workflow errors must belong to the same stage as StageResult."
                )

        return self


class WorkflowState(WorkflowBaseModel):
    """Complete deterministic state for one workflow execution."""

    workflow_id: UUID = Field(default_factory=uuid4)
    status: WorkflowStatus
    current_stage: WorkflowStage
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None
    stage_results: list[StageResult] = Field(default_factory=list)
    workflow_errors: list[WorkflowError] = Field(default_factory=list)
    retry_counts: dict[WorkflowStage, int] = Field(default_factory=dict)
    intake_result_id: UUID | None = None
    research_plan_id: UUID | None = None
    source_selection_id: UUID | None = None
    candidate_analysis_ids: list[UUID] = Field(default_factory=list)
    recommendation_id: UUID | None = None
    validation_id: UUID | None = None
    report_draft_id: UUID | None = None
    workflow_artifact_id: UUID | None = None
    final_report_artifact_ids: list[UUID] = Field(default_factory=list)

    @field_validator("started_at", "completed_at")
    @classmethod
    def validate_timezone_aware_timestamps(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require timezone information for workflow timestamps."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Workflow timestamps must be timezone-aware."
            )

        return value

    @field_validator("candidate_analysis_ids", "final_report_artifact_ids")
    @classmethod
    def validate_unique_record_ids(
        cls,
        identifiers: list[UUID],
    ) -> list[UUID]:
        """Reject duplicate workflow-level record identifiers."""

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Workflow record identifiers must be unique."
            )

        return identifiers

    @field_validator("retry_counts")
    @classmethod
    def validate_retry_counts(
        cls,
        retry_counts: dict[WorkflowStage, int],
    ) -> dict[WorkflowStage, int]:
        """Require nonnegative retry counts."""

        if any(count < 0 for count in retry_counts.values()):
            raise ValueError(
                "Workflow retry counts cannot be negative."
            )

        return retry_counts

    @model_validator(mode="after")
    def validate_workflow_state(self) -> "WorkflowState":
        """Validate workflow status, timestamps, and nested records."""

        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError(
                "Workflow completion time cannot precede start time."
            )

        terminal_statuses = {
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        }
        nonterminal_statuses = {
            WorkflowStatus.NOT_STARTED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING_FOR_CLARIFICATION,
            WorkflowStatus.CORRECTION_REQUIRED,
        }

        if self.status in terminal_statuses and self.completed_at is None:
            raise ValueError(
                "A terminal workflow requires a completion timestamp."
            )

        if self.status in nonterminal_statuses and self.completed_at is not None:
            raise ValueError(
                "A nonterminal workflow cannot have a completion timestamp."
            )

        stage_result_ids = [result.stage_result_id for result in self.stage_results]
        if len(stage_result_ids) != len(set(stage_result_ids)):
            raise ValueError("Stage-result identifiers must be unique.")

        for result in self.stage_results:
            if result.workflow_id != self.workflow_id:
                raise ValueError(
                    "Stage results must use the same workflow_id as WorkflowState."
                )

        workflow_error_ids = [error.error_id for error in self.workflow_errors]
        if len(workflow_error_ids) != len(set(workflow_error_ids)):
            raise ValueError(
                "Workflow-error identifiers must be unique within WorkflowState."
            )

        for error in self.workflow_errors:
            if error.workflow_id != self.workflow_id:
                raise ValueError(
                    "Workflow errors must use the same workflow_id as WorkflowState."
                )

        if self.status == WorkflowStatus.FAILED and not self.workflow_errors:
            raise ValueError(
                "A failed workflow requires at least one structured workflow error."
            )

        if self.status == WorkflowStatus.COMPLETED and self.workflow_artifact_id is None:
            raise ValueError(
                "A completed workflow requires a workflow artifact."
            )

        if self.status == WorkflowStatus.COMPLETED and not self.final_report_artifact_ids:
            raise ValueError(
                "A completed workflow requires final report artifact identifiers."
            )

        return self
