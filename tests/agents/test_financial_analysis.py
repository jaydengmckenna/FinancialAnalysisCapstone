"""Focused offline tests for the Financial Analysis Agent boundary."""

from decimal import Decimal
from uuid import uuid4

from fin_automation.agents.financial_analysis import FinancialAnalysisAgent
from fin_automation.models.common import SearchPurpose, SourceCategory
from fin_automation.models.research import EvidenceRequirement
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


def _make_requirement() -> EvidenceRequirement:
    return EvidenceRequirement(
        candidate_name="Build-A-Bear Workshop",
        name="Gross profit growth FY2023 to FY2024",
        description="Gross profit growth from FY2023 to FY2024.",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.SECONDARY],
    )


def _make_evidence(
    workflow_id,
    requirement_id,
    *,
    reported_value: Decimal,
    currency: str | None,
    unit: str | None,
    reporting_period: str | None = None,
) -> ExtractedEvidence:
    return ExtractedEvidence(
        workflow_id=workflow_id,
        source_id=uuid4(),
        evidence_requirement_id=requirement_id,
        evidence_type="gross_profit",
        content="Extracted gross profit figure.",
        reported_value=reported_value,
        currency=currency,
        unit=unit,
        reporting_period=reporting_period,
    )


def test_is_covered_true_when_both_requested_years_have_dollar_evidence() -> None:
    workflow_id = uuid4()
    requirement = _make_requirement()
    evidence = [
        _make_evidence(
            workflow_id,
            requirement.requirement_id,
            reported_value=Decimal("245.9"),
            currency="USD",
            unit="million",
            reporting_period="FY2023",
        ),
        _make_evidence(
            workflow_id,
            requirement.requirement_id,
            reported_value=Decimal("264.4"),
            currency="USD",
            unit="million",
            reporting_period="FY2024",
        ),
    ]

    assert FinancialAnalysisAgent._is_covered(requirement, evidence) is True


def test_is_covered_false_when_only_one_of_two_requested_years_present() -> None:
    """Regression: a combined "FY2023 to FY2024" requirement with only
    one year's evidence must not be treated as covered — the National
    Presto Industries live run showed this exact pattern (a bundle of
    evidence for the wrong years) getting waved through as "covered"
    before this check existed."""

    workflow_id = uuid4()
    requirement = _make_requirement()
    evidence = [
        _make_evidence(
            workflow_id,
            requirement.requirement_id,
            reported_value=Decimal("245.9"),
            currency="USD",
            unit="million",
            reporting_period="FY2023",
        ),
    ]

    assert FinancialAnalysisAgent._is_covered(requirement, evidence) is False


def test_is_covered_false_when_evidence_is_for_a_different_year() -> None:
    workflow_id = uuid4()
    requirement = _make_requirement()
    evidence = [
        _make_evidence(
            workflow_id,
            requirement.requirement_id,
            reported_value=Decimal("33.1"),
            currency="USD",
            unit="million",
            reporting_period="Fiscal Year 2025",
        ),
    ]

    assert FinancialAnalysisAgent._is_covered(requirement, evidence) is False


def test_is_covered_false_for_percentage_unit_even_with_currency() -> None:
    workflow_id = uuid4()
    requirement = _make_requirement()
    evidence = [
        _make_evidence(
            workflow_id,
            requirement.requirement_id,
            reported_value=Decimal("11.9"),
            currency="USD",
            unit="percent",
            reporting_period="FY2023",
        ),
    ]

    assert FinancialAnalysisAgent._is_covered(requirement, evidence) is False


def test_is_covered_false_when_currency_missing() -> None:
    workflow_id = uuid4()
    requirement = _make_requirement()
    evidence = [
        _make_evidence(
            workflow_id,
            requirement.requirement_id,
            reported_value=Decimal("55.2"),
            currency=None,
            unit="%",
            reporting_period="FY2023",
        ),
    ]

    assert FinancialAnalysisAgent._is_covered(requirement, evidence) is False


def test_is_covered_false_when_no_evidence_matches_requirement() -> None:
    requirement = _make_requirement()

    assert FinancialAnalysisAgent._is_covered(requirement, []) is False


def test_is_covered_true_for_dollar_evidence_when_requirement_has_no_year() -> None:
    workflow_id = uuid4()
    requirement = EvidenceRequirement(
        candidate_name="Build-A-Bear Workshop",
        name="Gross profit growth",
        description="Gross profit growth.",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.SECONDARY],
    )
    evidence = [
        _make_evidence(
            workflow_id,
            requirement.requirement_id,
            reported_value=Decimal("264.4"),
            currency="USD",
            unit="million",
        ),
    ]

    assert FinancialAnalysisAgent._is_covered(requirement, evidence) is True


def test_is_percentage_unit_detects_percent_variants() -> None:
    assert FinancialAnalysisAgent._is_percentage_unit("%") is True
    assert FinancialAnalysisAgent._is_percentage_unit("percent") is True
    assert FinancialAnalysisAgent._is_percentage_unit("Percent") is True
    assert FinancialAnalysisAgent._is_percentage_unit("billion") is False
    assert FinancialAnalysisAgent._is_percentage_unit(None) is False


def test_extract_years_finds_all_distinct_years_in_order() -> None:
    requirement = _make_requirement()

    assert FinancialAnalysisAgent._extract_years(requirement) == [2023, 2024]


def test_extract_years_empty_when_no_year_mentioned() -> None:
    requirement = EvidenceRequirement(
        candidate_name="Build-A-Bear Workshop",
        name="Gross profit growth",
        description="Gross profit growth.",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[SourceCategory.SECONDARY],
    )

    assert FinancialAnalysisAgent._extract_years(requirement) == []
