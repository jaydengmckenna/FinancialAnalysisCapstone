"""Focused offline tests for the Financial Analysis Agent boundary."""

from decimal import Decimal
from uuid import uuid4

from fin_automation.models.sources import ExtractedEvidence
from fin_automation.prompts.financial_analysis import build_financial_analysis_task


def test_prompt_contains_evidence_ids_and_values() -> None:
    workflow_id = uuid4()
    evidence = ExtractedEvidence(
        workflow_id=workflow_id,
        source_id=uuid4(),
        candidate_name="Microsoft",
        evidence_type="revenue",
        content="Microsoft reported revenue of $281.7 billion.",
        reported_value=Decimal("281.7"),
        currency="USD",
        unit="billion",
        reporting_period="FY2025",
    )
    task = build_financial_analysis_task([evidence])
    assert str(evidence.evidence_id) in task
    assert "281.7" in task
    assert "Microsoft" in task
