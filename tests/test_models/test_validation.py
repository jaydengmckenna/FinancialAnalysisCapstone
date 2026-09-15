"""Tests for evidence-validation data contracts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from fin_automation.models.common import (
    CorrectionTarget,
    SearchPurpose,
    ValidationCategory,
    ValidationOutcome,
    ValidationSeverity,
    WorkflowStage,
)
from fin_automation.models.research import (
    AdditionalResearchRequest,
)
from fin_automation.models.validation import (
    ValidationClaim,
    ValidationFinding,
    ValidationResult,
)


def create_warning_finding(
    workflow_id: UUID,
) -> ValidationFinding:
    """Create a valid warning-level finding."""

    return ValidationFinding(
        workflow_id=workflow_id,
        category=ValidationCategory.MISSING_EVIDENCE,
        severity=ValidationSeverity.WARNING,
        candidate_name="Company A",
        description=(
            "Current valuation evidence is incomplete."
        ),
        required_correction=(
            "Disclose the missing valuation evidence."
        ),
        correction_target=(
            CorrectionTarget.FINANCIAL_ANALYSIS
        ),
    )


def create_blocking_finding(
    workflow_id: UUID,
) -> ValidationFinding:
    """Create a valid blocking validation finding."""

    return ValidationFinding(
        workflow_id=workflow_id,
        category=ValidationCategory.UNSUPPORTED_CLAIM,
        severity=ValidationSeverity.BLOCKING,
        candidate_name="Company A",
        affected_claim=(
            "Company A has guaranteed long-term growth."
        ),
        source_ids=[uuid4()],
        evidence_ids=[uuid4()],
        description=(
            "The recommendation contains an unsupported claim."
        ),
        required_correction=(
            "Remove or qualify the unsupported claim."
        ),
        correction_target=(
            CorrectionTarget.FINANCIAL_ANALYSIS
        ),
    )


def create_additional_research_request(
    workflow_id: UUID,
) -> AdditionalResearchRequest:
    """Create a valid additional-research request."""

    return AdditionalResearchRequest(
        workflow_id=workflow_id,
        requested_by_stage=(
            WorkflowStage.EVIDENCE_VALIDATION
        ),
        candidate_name="Company A",
        missing_evidence="Current debt information",
        evidence_requirement_id=uuid4(),
        reason=(
            "The available source does not contain current "
            "balance-sheet evidence."
        ),
        suggested_search_purpose=(
            SearchPurpose.BALANCE_SHEET
        ),
        blocks_recommendation=True,
    )


def test_validation_finding_accepts_warning() -> None:
    """A warning-level validation finding should be accepted."""

    workflow_id = uuid4()
    finding = create_warning_finding(workflow_id)

    assert finding.workflow_id == workflow_id
    assert finding.severity == ValidationSeverity.WARNING
    assert finding.finding_id is not None


def test_validation_claim_requires_traceable_reference() -> None:
    """Claims cannot enter validation without a record reference."""

    with pytest.raises(
        ValidationError,
        match="requires source, evidence, or calculation references",
    ):
        ValidationClaim(
            workflow_id=uuid4(),
            text="A claim without a citation.",
        )


def test_calculated_claim_requires_expected_value() -> None:
    """Calculation-backed claims must expose the value being checked."""

    with pytest.raises(
        ValidationError,
        match="requires expected_value",
    ):
        ValidationClaim(
            workflow_id=uuid4(),
            text="Revenue grew.",
            calculation_id=uuid4(),
            expected_unit="percent",
            expected_value=None,
        )


def test_blocking_finding_requires_correction() -> None:
    """A blocking finding requires correction instructions."""

    with pytest.raises(
        ValidationError,
        match="blocking finding requires a correction",
    ):
        ValidationFinding(
            workflow_id=uuid4(),
            category=ValidationCategory.MISSING_EVIDENCE,
            severity=ValidationSeverity.BLOCKING,
            description="Required evidence is missing.",
            correction_target=(
                CorrectionTarget.FINANCIAL_ANALYSIS
            ),
        )


def test_unsupported_claim_requires_affected_claim() -> None:
    """Unsupported-claim findings must identify the claim."""

    with pytest.raises(
        ValidationError,
        match="must identify the affected claim",
    ):
        ValidationFinding(
            workflow_id=uuid4(),
            category=ValidationCategory.UNSUPPORTED_CLAIM,
            severity=ValidationSeverity.ERROR,
            description="A claim is unsupported.",
            required_correction="Remove the unsupported claim.",
            correction_target=(
                CorrectionTarget.FINANCIAL_ANALYSIS
            ),
        )


def test_calculation_problem_requires_calculation_id() -> None:
    """Calculation-input findings must identify the calculation."""

    with pytest.raises(
        ValidationError,
        match="must identify the affected calculation",
    ):
        ValidationFinding(
            workflow_id=uuid4(),
            category=(
                ValidationCategory.CALCULATION_INPUT_PROBLEM
            ),
            severity=ValidationSeverity.ERROR,
            description="The calculation uses invalid inputs.",
            required_correction=(
                "Correct the calculation inputs."
            ),
            correction_target=(
                CorrectionTarget.FINANCIAL_CALCULATION
            ),
        )


@pytest.mark.parametrize(
    "category",
    [
        ValidationCategory.INVALID_CITATION,
        ValidationCategory.IRRELEVANT_CITATION,
    ],
)
def test_citation_finding_requires_record_reference(
    category: ValidationCategory,
) -> None:
    """Citation findings must reference a record."""

    with pytest.raises(
        ValidationError,
        match=(
            "must reference at least one source or evidence record"
        ),
    ):
        ValidationFinding(
            workflow_id=uuid4(),
            category=category,
            severity=ValidationSeverity.ERROR,
            description="The citation does not support the claim.",
            required_correction="Replace the citation.",
            correction_target=(
                CorrectionTarget.FINANCIAL_ANALYSIS
            ),
        )


def test_validation_finding_rejects_duplicate_source_ids() -> None:
    """Validation findings should reject duplicate source IDs."""

    source_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="identifiers must be unique",
    ):
        ValidationFinding(
            workflow_id=uuid4(),
            category=ValidationCategory.INVALID_CITATION,
            severity=ValidationSeverity.ERROR,
            source_ids=[source_id, source_id],
            description="The citation is invalid.",
            required_correction="Replace the citation.",
            correction_target=(
                CorrectionTarget.FINANCIAL_ANALYSIS
            ),
        )


def test_approved_validation_result_accepts_valid_records() -> None:
    """An approved result may contain nonblocking findings."""

    workflow_id = uuid4()

    result = ValidationResult(
        workflow_id=workflow_id,
        recommendation_id=uuid4(),
        outcome=ValidationOutcome.APPROVED,
        findings=[create_warning_finding(workflow_id)],
        approved_candidate_analysis_ids=[uuid4()],
        approved_source_ids=[uuid4()],
        approved_evidence_ids=[uuid4()],
        approved_calculation_ids=[uuid4()],
        summary=(
            "The recommendation is supported by the approved "
            "records."
        ),
    )

    assert result.outcome == ValidationOutcome.APPROVED
    assert result.validated_at.tzinfo is not None
    assert result.validated_at.utcoffset() is not None


def test_approved_result_rejects_blocking_finding() -> None:
    """Approved validation cannot contain blocking findings."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="cannot contain blocking findings",
    ):
        ValidationResult(
            workflow_id=workflow_id,
            recommendation_id=uuid4(),
            outcome=ValidationOutcome.APPROVED,
            findings=[create_blocking_finding(workflow_id)],
            summary="The recommendation was evaluated.",
        )


def test_analysis_correction_requires_finding() -> None:
    """Analysis-correction outcome requires a finding."""

    with pytest.raises(
        ValidationError,
        match=(
            "Analysis correction requires at least one "
            "validation finding"
        ),
    ):
        ValidationResult(
            workflow_id=uuid4(),
            recommendation_id=uuid4(),
            outcome=(
                ValidationOutcome.ANALYSIS_CORRECTION_REQUIRED
            ),
            findings=[],
            summary="Analysis correction is required.",
        )


def test_analysis_correction_accepts_finding() -> None:
    """Analysis correction should accept a correction finding."""

    workflow_id = uuid4()

    result = ValidationResult(
        workflow_id=workflow_id,
        recommendation_id=uuid4(),
        outcome=(
            ValidationOutcome.ANALYSIS_CORRECTION_REQUIRED
        ),
        findings=[create_blocking_finding(workflow_id)],
        summary=(
            "The unsupported claim must be corrected."
        ),
    )

    assert (
        result.outcome
        == ValidationOutcome.ANALYSIS_CORRECTION_REQUIRED
    )
    assert len(result.findings) == 1


def test_additional_research_requires_request() -> None:
    """Additional-research outcome requires a research request."""

    with pytest.raises(
        ValidationError,
        match=(
            "requires at least one additional research request"
        ),
    ):
        ValidationResult(
            workflow_id=uuid4(),
            recommendation_id=uuid4(),
            outcome=(
                ValidationOutcome.ADDITIONAL_RESEARCH_REQUIRED
            ),
            summary="Additional research is required.",
        )


def test_additional_research_accepts_request() -> None:
    """Additional-research outcome should accept a valid request."""

    workflow_id = uuid4()

    result = ValidationResult(
        workflow_id=workflow_id,
        recommendation_id=uuid4(),
        outcome=(
            ValidationOutcome.ADDITIONAL_RESEARCH_REQUIRED
        ),
        findings=[create_warning_finding(workflow_id)],
        additional_research_requests=[
            create_additional_research_request(workflow_id)
        ],
        summary=(
            "Current debt evidence must be collected."
        ),
    )

    assert (
        result.outcome
        == ValidationOutcome.ADDITIONAL_RESEARCH_REQUIRED
    )
    assert len(result.additional_research_requests) == 1


def test_insufficient_evidence_result_accepts_valid_data() -> None:
    """Insufficient-evidence outcome may document evidence gaps."""

    workflow_id = uuid4()

    result = ValidationResult(
        workflow_id=workflow_id,
        recommendation_id=uuid4(),
        outcome=ValidationOutcome.INSUFFICIENT_EVIDENCE,
        findings=[create_warning_finding(workflow_id)],
        summary=(
            "The available evidence is insufficient to support "
            "a recommendation."
        ),
    )

    assert (
        result.outcome
        == ValidationOutcome.INSUFFICIENT_EVIDENCE
    )
    assert len(result.findings) == 1


def test_rejected_result_requires_blocking_finding() -> None:
    """Rejected validation requires a blocking finding."""

    workflow_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="requires at least one blocking finding",
    ):
        ValidationResult(
            workflow_id=workflow_id,
            recommendation_id=uuid4(),
            outcome=ValidationOutcome.REJECTED,
            findings=[create_warning_finding(workflow_id)],
            summary="The validation result was rejected.",
        )


def test_rejected_result_accepts_blocking_finding() -> None:
    """Rejected outcome should accept a blocking finding."""

    workflow_id = uuid4()

    result = ValidationResult(
        workflow_id=workflow_id,
        recommendation_id=uuid4(),
        outcome=ValidationOutcome.REJECTED,
        findings=[create_blocking_finding(workflow_id)],
        summary=(
            "The recommendation cannot proceed in its current form."
        ),
    )

    assert result.outcome == ValidationOutcome.REJECTED
    assert (
        result.findings[0].severity
        == ValidationSeverity.BLOCKING
    )


def test_finding_must_use_same_workflow() -> None:
    """Nested findings must belong to the same workflow."""

    with pytest.raises(
        ValidationError,
        match="must use the same workflow_id",
    ):
        ValidationResult(
            workflow_id=uuid4(),
            recommendation_id=uuid4(),
            outcome=(
                ValidationOutcome.ANALYSIS_CORRECTION_REQUIRED
            ),
            findings=[
                create_blocking_finding(uuid4())
            ],
            summary="Analysis correction is required.",
        )


def test_research_request_must_use_same_workflow() -> None:
    """Additional research requests must match the workflow."""

    with pytest.raises(
        ValidationError,
        match="must use the same workflow_id",
    ):
        ValidationResult(
            workflow_id=uuid4(),
            recommendation_id=uuid4(),
            outcome=(
                ValidationOutcome.ADDITIONAL_RESEARCH_REQUIRED
            ),
            additional_research_requests=[
                create_additional_research_request(uuid4())
            ],
            summary="Additional research is required.",
        )


def test_approved_identifiers_must_be_unique() -> None:
    """Approved-record identifier lists must be unique."""

    analysis_id = uuid4()

    with pytest.raises(
        ValidationError,
        match="Approved record identifiers must be unique",
    ):
        ValidationResult(
            workflow_id=uuid4(),
            recommendation_id=uuid4(),
            outcome=ValidationOutcome.APPROVED,
            approved_candidate_analysis_ids=[
                analysis_id,
                analysis_id,
            ],
            summary="The recommendation is approved.",
        )


def test_validation_result_rejects_duplicate_findings() -> None:
    """A finding should appear only once in a validation result."""

    workflow_id = uuid4()
    finding = create_warning_finding(workflow_id)

    with pytest.raises(
        ValidationError,
        match=(
            "Validation-finding identifiers must be unique "
            "within ValidationResult"
        ),
    ):
        ValidationResult(
            workflow_id=workflow_id,
            recommendation_id=uuid4(),
            outcome=ValidationOutcome.APPROVED,
            findings=[
                finding,
                finding.model_copy(deep=True),
            ],
            summary="The recommendation was validated.",
        )


def test_validation_result_rejects_naive_timestamp() -> None:
    """Validation timestamps must be timezone-aware."""

    with pytest.raises(
        ValidationError,
        match="validated_at must be timezone-aware",
    ):
        ValidationResult(
            workflow_id=uuid4(),
            recommendation_id=uuid4(),
            outcome=ValidationOutcome.APPROVED,
            summary="The recommendation is approved.",
            validated_at=datetime(2026, 9, 11, 10, 0, 0),
        )


def test_validation_models_reject_unknown_fields() -> None:
    """Validation contracts should reject undocumented fields."""

    with pytest.raises(ValidationError):
        ValidationFinding(
            workflow_id=uuid4(),
            category=ValidationCategory.MISSING_EVIDENCE,
            severity=ValidationSeverity.WARNING,
            description="Evidence is missing.",
            correction_target=(
                CorrectionTarget.FINANCIAL_ANALYSIS
            ),
            undocumented_field="unexpected value",
        )


def test_validation_finding_serialization_round_trip() -> None:
    """A validation finding should serialize and reconstruct."""

    finding = create_blocking_finding(uuid4())

    serialized = finding.model_dump_json()
    reconstructed = ValidationFinding.model_validate_json(
        serialized
    )

    assert reconstructed == finding


def test_validation_result_serialization_round_trip() -> None:
    """A validation result should serialize and reconstruct."""

    workflow_id = uuid4()

    result = ValidationResult(
        workflow_id=workflow_id,
        recommendation_id=uuid4(),
        outcome=ValidationOutcome.APPROVED,
        findings=[create_warning_finding(workflow_id)],
        approved_candidate_analysis_ids=[uuid4()],
        approved_source_ids=[uuid4()],
        approved_evidence_ids=[uuid4()],
        approved_calculation_ids=[uuid4()],
        summary=(
            "The recommendation is supported by the approved "
            "records."
        ),
    )

    serialized = result.model_dump_json()
    reconstructed = ValidationResult.model_validate_json(
        serialized
    )

    assert reconstructed == result