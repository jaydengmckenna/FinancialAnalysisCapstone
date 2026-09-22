"""Tests for deterministic workflow-state contracts."""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fin_automation.models.common import (
    ErrorSeverity,
    StageStatus,
    WorkflowStage,
    WorkflowStatus,
)
from fin_automation.models.workflow import (
    StageResult,
    WorkflowErrorRecord,
    WorkflowState,
)


def create_recoverable_error(
    workflow_id: UUID,
    stage: WorkflowStage = WorkflowStage.WEB_RETRIEVAL,
) -> WorkflowErrorRecord:
    """Create a valid recoverable workflow error."""

    return WorkflowErrorRecord(
        workflow_id=workflow_id,
        stage=stage,
        severity=ErrorSeverity.ERROR,
        error_type="RetrievalError",
        message="The selected webpage could not be retrieved.",
        recoverable=True,
        retry_allowed=True,
        retry_count=1,
        details={"reason": "HTTP request timed out"},
    )


def create_critical_error(
    workflow_id: UUID,
    stage: WorkflowStage = WorkflowStage.EVIDENCE_VALIDATION,
) -> WorkflowErrorRecord:
    """Create a valid nonrecoverable critical error."""

    return WorkflowErrorRecord(
        workflow_id=workflow_id,
        stage=stage,
        severity=ErrorSeverity.CRITICAL,
        error_type="EvidenceValidationError",
        message="A blocking validation failure prevents completion.",
        recoverable=False,
        retry_allowed=False,
        retry_count=0,
    )


def create_completed_stage(
    workflow_id: UUID,
    stage: WorkflowStage = WorkflowStage.RESEARCH_PLANNING,
) -> StageResult:
    """Create a valid completed stage result."""

    started_at = datetime.now(timezone.utc)
    return StageResult(
        workflow_id=workflow_id,
        stage=stage,
        status=StageStatus.COMPLETED,
        attempt_number=1,
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=1),
        produced_record_ids=[uuid4()],
        summary="The stage completed successfully.",
    )


def test_workflow_error_accepts_recoverable_error() -> None:
    workflow_id = uuid4()
    error = create_recoverable_error(workflow_id)
    assert error.workflow_id == workflow_id
    assert error.retry_allowed is True
    assert error.retry_count == 1


def test_nonrecoverable_error_rejects_retry() -> None:
    with pytest.raises(ValidationError, match="nonrecoverable error cannot allow retry"):
        WorkflowErrorRecord(
            workflow_id=uuid4(),
            stage=WorkflowStage.WEB_RETRIEVAL,
            severity=ErrorSeverity.ERROR,
            error_type="RetrievalError",
            message="The operation cannot continue.",
            recoverable=False,
            retry_allowed=True,
        )


def test_positive_retry_count_requires_retry_allowed() -> None:
    with pytest.raises(ValidationError, match="positive retry count requires retry_allowed"):
        WorkflowErrorRecord(
            workflow_id=uuid4(),
            stage=WorkflowStage.WEB_RETRIEVAL,
            severity=ErrorSeverity.ERROR,
            error_type="RetrievalError",
            message="The operation failed.",
            recoverable=True,
            retry_allowed=False,
            retry_count=1,
        )


def test_critical_error_cannot_be_recoverable() -> None:
    with pytest.raises(ValidationError, match="critical workflow error cannot be recoverable"):
        WorkflowErrorRecord(
            workflow_id=uuid4(),
            stage=WorkflowStage.EVIDENCE_VALIDATION,
            severity=ErrorSeverity.CRITICAL,
            error_type="EvidenceValidationError",
            message="A critical validation failure occurred.",
            recoverable=True,
            retry_allowed=True,
        )


def test_completed_stage_accepts_valid_data() -> None:
    workflow_id = uuid4()
    result = create_completed_stage(workflow_id)
    assert result.status == StageStatus.COMPLETED
    assert result.completed_at is not None


def test_terminal_stage_requires_completion_timestamp() -> None:
    with pytest.raises(ValidationError, match="terminal stage requires a completion timestamp"):
        StageResult(
            workflow_id=uuid4(),
            stage=WorkflowStage.RESEARCH_PLANNING,
            status=StageStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
        )


def test_nonterminal_stage_rejects_completion_timestamp() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="nonterminal stage cannot have a completion"):
        StageResult(
            workflow_id=uuid4(),
            stage=WorkflowStage.WEB_SEARCH,
            status=StageStatus.IN_PROGRESS,
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=1),
        )


def test_stage_completion_cannot_precede_start() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="cannot precede start time"):
        StageResult(
            workflow_id=uuid4(),
            stage=WorkflowStage.WEB_SEARCH,
            status=StageStatus.COMPLETED,
            started_at=started_at,
            completed_at=started_at - timedelta(seconds=1),
        )


def test_failed_stage_requires_error() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="failed stage requires at least one workflow error"):
        StageResult(
            workflow_id=uuid4(),
            stage=WorkflowStage.WEB_RETRIEVAL,
            status=StageStatus.FAILED,
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=1),
        )


def test_failed_stage_accepts_matching_error() -> None:
    workflow_id = uuid4()
    started_at = datetime.now(timezone.utc)
    result = StageResult(
        workflow_id=workflow_id,
        stage=WorkflowStage.WEB_RETRIEVAL,
        status=StageStatus.FAILED,
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=1),
        errors=[create_recoverable_error(workflow_id)],
    )
    assert len(result.errors) == 1


def test_completed_stage_rejects_errors() -> None:
    workflow_id = uuid4()
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="cannot contain workflow errors"):
        StageResult(
            workflow_id=workflow_id,
            stage=WorkflowStage.WEB_RETRIEVAL,
            status=StageStatus.COMPLETED,
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=1),
            errors=[create_recoverable_error(workflow_id)],
        )


def test_stage_error_must_match_workflow() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="must use the same workflow_id"):
        StageResult(
            workflow_id=uuid4(),
            stage=WorkflowStage.WEB_RETRIEVAL,
            status=StageStatus.FAILED,
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=1),
            errors=[create_recoverable_error(uuid4())],
        )


def test_stage_error_must_match_stage() -> None:
    workflow_id = uuid4()
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="must belong to the same stage"):
        StageResult(
            workflow_id=workflow_id,
            stage=WorkflowStage.WEB_SEARCH,
            status=StageStatus.FAILED,
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=1),
            errors=[create_recoverable_error(workflow_id, WorkflowStage.WEB_RETRIEVAL)],
        )


def test_stage_rejects_duplicate_record_ids() -> None:
    record_id = uuid4()
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="Produced record identifiers must be unique"):
        StageResult(
            workflow_id=uuid4(),
            stage=WorkflowStage.RESEARCH_PLANNING,
            status=StageStatus.COMPLETED,
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=1),
            produced_record_ids=[record_id, record_id],
        )


def test_in_progress_workflow_accepts_valid_data() -> None:
    workflow_id = uuid4()
    state = WorkflowState(
        workflow_id=workflow_id,
        status=WorkflowStatus.IN_PROGRESS,
        current_stage=WorkflowStage.WEB_SEARCH,
        stage_results=[create_completed_stage(workflow_id)],
        retry_counts={WorkflowStage.WEB_SEARCH: 0},
        intake_result_id=uuid4(),
        research_plan_id=uuid4(),
    )
    assert state.completed_at is None


def test_terminal_workflow_requires_completion_timestamp() -> None:
    with pytest.raises(ValidationError, match="terminal workflow requires a completion timestamp"):
        WorkflowState(
            status=WorkflowStatus.COMPLETED,
            current_stage=WorkflowStage.HUMAN_REVIEW,
            workflow_artifact_id=uuid4(),
            final_report_artifact_ids=[uuid4()],
        )


def test_nonterminal_workflow_rejects_completion_timestamp() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="nonterminal workflow cannot have a completion"):
        WorkflowState(
            status=WorkflowStatus.IN_PROGRESS,
            current_stage=WorkflowStage.WEB_SEARCH,
            completed_at=started_at + timedelta(seconds=1.0),
        )


def test_completed_workflow_requires_workflow_artifact() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="requires a workflow artifact"):
        WorkflowState(
            status=WorkflowStatus.COMPLETED,
            current_stage=WorkflowStage.HUMAN_REVIEW,
            completed_at=started_at + timedelta(seconds=1.0),
            final_report_artifact_ids=[uuid4()],
        )


def test_completed_workflow_requires_report_artifacts() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="requires final report artifact identifiers"):
        WorkflowState(
            status=WorkflowStatus.COMPLETED,
            current_stage=WorkflowStage.HUMAN_REVIEW,
            completed_at=started_at + timedelta(seconds=1.0),
            workflow_artifact_id=uuid4(),
        )


def test_completed_workflow_accepts_final_artifacts() -> None:
    started_at = datetime.now(timezone.utc)
    state = WorkflowState(
        status=WorkflowStatus.COMPLETED,
        current_stage=WorkflowStage.HUMAN_REVIEW,
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=1),
        workflow_artifact_id=uuid4(),
        final_report_artifact_ids=[uuid4(), uuid4()],
    )
    assert state.status == WorkflowStatus.COMPLETED


def test_failed_workflow_requires_error() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="failed workflow requires at least one structured"):
        WorkflowState(
            status=WorkflowStatus.FAILED,
            current_stage=WorkflowStage.EVIDENCE_VALIDATION,
            completed_at=started_at + timedelta(seconds=1.0),
        )


def test_failed_workflow_accepts_critical_error() -> None:
    started_at = datetime.now(timezone.utc)
    workflow_id = uuid4()
    state = WorkflowState(
        workflow_id=workflow_id,
        status=WorkflowStatus.FAILED,
        current_stage=WorkflowStage.EVIDENCE_VALIDATION,
        completed_at=started_at + timedelta(seconds=1.0),
        workflow_errors=[create_critical_error(workflow_id)],
    )
    assert len(state.workflow_errors) == 1


def test_stage_result_must_match_workflow() -> None:
    with pytest.raises(ValidationError, match="Stage results must use the same workflow_id"):
        WorkflowState(
            workflow_id=uuid4(),
            status=WorkflowStatus.IN_PROGRESS,
            current_stage=WorkflowStage.WEB_SEARCH,
            stage_results=[create_completed_stage(uuid4())],
        )


def test_workflow_error_must_match_workflow() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="Workflow errors must use the same workflow_id"):
        WorkflowState(
            workflow_id=uuid4(),
            status=WorkflowStatus.FAILED,
            current_stage=WorkflowStage.EVIDENCE_VALIDATION,
            completed_at=started_at + timedelta(seconds=1.0),
            workflow_errors=[create_critical_error(uuid4())],
        )


def test_workflow_rejects_negative_retry_count() -> None:
    with pytest.raises(ValidationError, match="retry counts cannot be negative"):
        WorkflowState(
            status=WorkflowStatus.IN_PROGRESS,
            current_stage=WorkflowStage.WEB_SEARCH,
            retry_counts={WorkflowStage.WEB_SEARCH: -1},
        )


def test_workflow_rejects_duplicate_analysis_ids() -> None:
    analysis_id = uuid4()
    with pytest.raises(ValidationError, match="Workflow record identifiers must be unique"):
        WorkflowState(
            status=WorkflowStatus.IN_PROGRESS,
            current_stage=WorkflowStage.FINANCIAL_ANALYSIS,
            candidate_analysis_ids=[analysis_id, analysis_id],
        )


def test_workflow_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        WorkflowState(
            status=WorkflowStatus.IN_PROGRESS,
            current_stage=WorkflowStage.WEB_SEARCH,
            undocumented_field="unexpected value",
        )


def test_workflow_error_serialization_round_trip() -> None:
    error = create_recoverable_error(uuid4())
    reconstructed = WorkflowErrorRecord.model_validate_json(error.model_dump_json())
    assert reconstructed == error


def test_workflow_state_serialization_round_trip() -> None:
    workflow_id = uuid4()
    state = WorkflowState(
        workflow_id=workflow_id,
        status=WorkflowStatus.IN_PROGRESS,
        current_stage=WorkflowStage.WEB_SEARCH,
        stage_results=[create_completed_stage(workflow_id)],
        retry_counts={WorkflowStage.WEB_SEARCH: 0},
        intake_result_id=uuid4(),
        research_plan_id=uuid4(),
    )
    reconstructed = WorkflowState.model_validate_json(state.model_dump_json())
    assert reconstructed == state
