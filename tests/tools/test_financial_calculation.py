"""Tests for deterministic Phase 6 calculations."""

from decimal import Decimal
from uuid import uuid4

import pytest

from fin_automation.models.sources import ExtractedEvidence
from fin_automation.tools.financial_calculation import FinancialCalculationTool


def make_evidence(*, workflow_id, value, candidate="Microsoft", currency="USD", unit="billion", period="FY2025"):
    return ExtractedEvidence(
        workflow_id=workflow_id,
        source_id=uuid4(),
        candidate_name=candidate,
        evidence_type="revenue",
        content=f"Reported value: {value}",
        reported_value=Decimal(value),
        currency=currency,
        unit=unit,
        reporting_period=period,
    )


def test_growth_rate_uses_authoritative_evidence() -> None:
    workflow_id = uuid4()
    current = make_evidence(workflow_id=workflow_id, value="281.7", period="FY2025")
    previous = make_evidence(workflow_id=workflow_id, value="245.1", period="FY2024")
    tool = FinancialCalculationTool()
    tool.begin_run(workflow_id, [current, previous])

    tool.forward({
        "operation": "growth_rate",
        "metric_name": "revenue growth",
        "first_evidence_id": str(current.evidence_id),
        "second_evidence_id": str(previous.evidence_id),
    })

    assert tool.accepted_calculations[0].value == Decimal("14.93")
    assert tool.accepted_calculations[0].input_evidence_ids == [current.evidence_id, previous.evidence_id]


def test_difference_allows_two_candidates() -> None:
    workflow_id = uuid4()
    first = make_evidence(workflow_id=workflow_id, value="281.7", candidate="Microsoft")
    second = make_evidence(workflow_id=workflow_id, value="250.0", candidate="Example")
    tool = FinancialCalculationTool()
    tool.begin_run(workflow_id, [first, second])
    tool.forward({
        "operation": "difference",
        "metric_name": "revenue difference",
        "first_evidence_id": str(first.evidence_id),
        "second_evidence_id": str(second.evidence_id),
    })
    assert tool.accepted_calculations[0].value == Decimal("31.70")


def test_zero_denominator_is_rejected() -> None:
    workflow_id = uuid4()
    first = make_evidence(workflow_id=workflow_id, value="10")
    second = make_evidence(workflow_id=workflow_id, value="0")
    tool = FinancialCalculationTool()
    tool.begin_run(workflow_id, [first, second])
    with pytest.raises(ValueError, match="zero denominator"):
        tool.forward({
            "operation": "ratio",
            "metric_name": "test ratio",
            "first_evidence_id": str(first.evidence_id),
            "second_evidence_id": str(second.evidence_id),
        })


def test_incompatible_units_are_rejected() -> None:
    workflow_id = uuid4()
    first = make_evidence(workflow_id=workflow_id, value="10", unit="billion")
    second = make_evidence(workflow_id=workflow_id, value="5", unit="million")
    tool = FinancialCalculationTool()
    tool.begin_run(workflow_id, [first, second])
    with pytest.raises(ValueError, match="matching units"):
        tool.forward({
            "operation": "difference",
            "metric_name": "revenue difference",
            "first_evidence_id": str(first.evidence_id),
            "second_evidence_id": str(second.evidence_id),
        })


def test_unauthorized_evidence_is_rejected() -> None:
    workflow_id = uuid4()
    first = make_evidence(workflow_id=workflow_id, value="10")
    second = make_evidence(workflow_id=workflow_id, value="5")
    tool = FinancialCalculationTool()
    tool.begin_run(workflow_id, [first, second])
    with pytest.raises(ValueError, match="unauthorized evidence"):
        tool.forward({
            "operation": "difference",
            "metric_name": "revenue difference",
            "first_evidence_id": str(first.evidence_id),
            "second_evidence_id": str(uuid4()),
        })
