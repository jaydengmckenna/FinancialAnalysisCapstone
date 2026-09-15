"""Deterministic financial-calculation tool for Phase 6."""

import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from smolagents import Tool

from fin_automation.models.financial import (
    CalculatedMetric,
    CalculationOperation,
)
from fin_automation.models.sources import ExtractedEvidence


_RESULT_QUANTUM = Decimal("0.01")


class FinancialCalculationTool(Tool):
    """Calculate one metric from two authorized evidence records."""

    name = "calculate_financial_metric"
    description = (
        "Performs one deterministic financial calculation using exactly "
        "two authorized extracted-evidence records. Supported operations "
        "are growth_rate, margin, ratio, and difference."
    )
    inputs = {
        "payload": {
            "type": "object",
            "description": (
                "Object containing operation, metric_name, "
                "first_evidence_id, and second_evidence_id. For "
                "growth_rate, the first evidence must be the current "
                "value and the second must be the previous value. For "
                "margin and ratio, the first evidence must be the "
                "numerator and the second must be the denominator. For "
                "difference, the second value is subtracted from the "
                "first value."
            ),
        }
    }
    output_type = "string"

    def __init__(self) -> None:
        """Initialize the deterministic calculation tool."""

        super().__init__()

        self._workflow_id: UUID | None = None
        self._evidence_by_id: dict[UUID, ExtractedEvidence] = {}
        self._accepted_calculations: list[CalculatedMetric] = []

    @property
    def accepted_calculations(self) -> list:
        """Return validated calculations from the current run."""

        return list(self._accepted_calculations)

    def begin_run(
        self,
        workflow_id: UUID,
        evidence: list[ExtractedEvidence],
    ) -> None:
        """Load authoritative evidence for one workflow."""

        if not evidence:
            raise ValueError(
                "Financial analysis requires extracted evidence."
            )

        if any(
            record.workflow_id != workflow_id
            for record in evidence
        ):
            raise ValueError(
                "All evidence must belong to the supplied workflow."
            )

        evidence_by_id = {
            record.evidence_id: record
            for record in evidence
        }

        if len(evidence_by_id) != len(evidence):
            raise ValueError(
                "Extracted evidence identifiers must be unique."
            )

        self._workflow_id = workflow_id
        self._evidence_by_id = evidence_by_id
        self._accepted_calculations = []

    def forward(
        self,
        payload: dict[str, Any],
    ) -> str:
        """Perform one validated financial calculation."""

        if self._workflow_id is None:
            raise RuntimeError(
                "begin_run() must be called before calculation."
            )

        (
            operation,
            metric_name,
            first_evidence_id,
            second_evidence_id,
        ) = self._parse_payload(payload)

        first_evidence = self._get_authorized_evidence(
            first_evidence_id
        )
        second_evidence = self._get_authorized_evidence(
            second_evidence_id
        )

        first_value = self._numeric_value(first_evidence)
        second_value = self._numeric_value(second_evidence)

        self._validate_compatibility(
            operation=operation,
            first=first_evidence,
            second=second_evidence,
        )

        (
            calculated_value,
            result_unit,
            result_currency,
            formula,
        ) = self._calculate(
            operation=operation,
            first_value=first_value,
            second_value=second_value,
            first_evidence=first_evidence,
        )

        candidate_names = self._candidate_names(
            first=first_evidence,
            second=second_evidence,
        )

        reporting_periods = self._reporting_periods(
            first=first_evidence,
            second=second_evidence,
        )

        calculation = CalculatedMetric(
            workflow_id=self._workflow_id,
            operation=operation,
            metric_name=metric_name,
            candidate_names=candidate_names,
            value=calculated_value,
            unit=result_unit,
            currency=result_currency,
            input_evidence_ids=[
                first_evidence_id,
                second_evidence_id,
            ],
            formula=formula,
            reporting_periods=reporting_periods,
            limitations=[],
        )

        self._accepted_calculations.append(calculation)

        return json.dumps(
            calculation.model_dump(mode="json"),
            indent=2,
        )

    @staticmethod
    def _parse_payload(
        payload: dict[str, Any],
    ) -> tuple[
        CalculationOperation,
        str,
        UUID,
        UUID,
    ]:
        """Parse and validate the agent-provided payload."""

        try:
            operation = CalculationOperation(
                payload["operation"]
            )
            metric_name = str(
                payload["metric_name"]
            ).strip()
            first_evidence_id = UUID(
                str(payload["first_evidence_id"])
            )
            second_evidence_id = UUID(
                str(payload["second_evidence_id"])
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid financial-calculation payload."
            ) from exc

        if not metric_name:
            raise ValueError(
                "metric_name must not be empty."
            )

        if first_evidence_id == second_evidence_id:
            raise ValueError(
                "A calculation requires two distinct evidence records."
            )

        return (
            operation,
            metric_name,
            first_evidence_id,
            second_evidence_id,
        )

    def _get_authorized_evidence(
        self,
        evidence_id: UUID,
    ) -> ExtractedEvidence:
        """Return evidence authorized for the current run."""

        try:
            return self._evidence_by_id[evidence_id]
        except KeyError as exc:
            raise ValueError(
                "The calculation referenced unauthorized evidence."
            ) from exc

    @staticmethod
    def _numeric_value(
        evidence: ExtractedEvidence,
    ) -> Decimal:
        """Return the authoritative numeric value from evidence."""

        if evidence.reported_value is None:
            raise ValueError(
                "Calculation evidence must contain a reported value."
            )

        try:
            return Decimal(str(evidence.reported_value))
        except InvalidOperation as exc:
            raise ValueError(
                "Evidence contains an invalid numeric value."
            ) from exc

    @staticmethod
    def _validate_compatibility(
        operation: CalculationOperation,
        first: ExtractedEvidence,
        second: ExtractedEvidence,
    ) -> None:
        """Validate that the evidence records can be calculated."""

        if not first.candidate_name:
            raise ValueError(
                "The first evidence record must identify a candidate."
            )

        if not second.candidate_name:
            raise ValueError(
                "The second evidence record must identify a candidate."
            )

        if first.currency != second.currency:
            raise ValueError(
                "Calculation evidence must use matching currencies."
            )

        if first.unit != second.unit:
            raise ValueError(
                "Calculation evidence must use matching units."
            )

        same_candidate = (
            first.candidate_name.casefold()
            == second.candidate_name.casefold()
        )

        if (
            operation != CalculationOperation.DIFFERENCE
            and not same_candidate
        ):
            raise ValueError(
                "Growth, margin, and ratio inputs must belong to "
                "the same candidate."
            )

        if (
            operation == CalculationOperation.GROWTH_RATE
            and first.reporting_period
            and second.reporting_period
            and first.reporting_period.casefold()
            == second.reporting_period.casefold()
        ):
            raise ValueError(
                "Growth rate requires two different reporting periods."
            )

    @staticmethod
    def _calculate(
        operation: CalculationOperation,
        first_value: Decimal,
        second_value: Decimal,
        first_evidence: ExtractedEvidence,
    ) -> tuple[
        Decimal,
        str | None,
        str | None,
        str,
    ]:
        """Execute one supported deterministic formula."""

        if operation == CalculationOperation.GROWTH_RATE:
            if second_value == 0:
                raise ValueError(
                    "Growth rate cannot use a zero previous value."
                )

            result = (
                (first_value - second_value)
                / second_value
                * Decimal("100")
            )

            return (
                result.quantize(
                    _RESULT_QUANTUM,
                    rounding=ROUND_HALF_UP,
                ),
                "percent",
                None,
                "((current - previous) / previous) * 100",
            )

        if operation == CalculationOperation.MARGIN:
            if second_value == 0:
                raise ValueError(
                    "Margin cannot use a zero denominator."
                )

            result = (
                first_value
                / second_value
                * Decimal("100")
            )

            return (
                result.quantize(
                    _RESULT_QUANTUM,
                    rounding=ROUND_HALF_UP,
                ),
                "percent",
                None,
                "(numerator / denominator) * 100",
            )

        if operation == CalculationOperation.RATIO:
            if second_value == 0:
                raise ValueError(
                    "Ratio cannot use a zero denominator."
                )

            result = first_value / second_value

            return (
                result.quantize(
                    _RESULT_QUANTUM,
                    rounding=ROUND_HALF_UP,
                ),
                "ratio",
                None,
                "numerator / denominator",
            )

        if operation == CalculationOperation.DIFFERENCE:
            result = first_value - second_value

            return (
                result.quantize(
                    _RESULT_QUANTUM,
                    rounding=ROUND_HALF_UP,
                ),
                first_evidence.unit,
                first_evidence.currency,
                "first - second",
            )

        raise ValueError(
            "The requested calculation operation is not implemented."
        )

    @staticmethod
    def _candidate_names(
        first: ExtractedEvidence,
        second: ExtractedEvidence,
    ) -> list:
        """Return unique candidate names from the calculation inputs."""

        candidate_names = list(
            dict.fromkeys(
                candidate_name
                for candidate_name in (
                    first.candidate_name,
                    second.candidate_name,
                )
                if candidate_name
            )
        )

        if not candidate_names:
            raise ValueError(
                "Calculation evidence must identify a candidate."
            )

        return candidate_names

    @staticmethod
    def _reporting_periods(
        first: ExtractedEvidence,
        second: ExtractedEvidence,
    ) -> list:
        """Return unique reporting periods from the inputs."""

        return list(
            dict.fromkeys(
                reporting_period
                for reporting_period in (
                    first.reporting_period,
                    second.reporting_period,
                )
                if reporting_period
            )
        )