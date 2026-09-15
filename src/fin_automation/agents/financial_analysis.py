"""Minimal Financial Analysis Agent for Phase 6."""

from uuid import UUID

from smolagents import Model, ToolCallingAgent

from fin_automation.models.financial import CalculatedMetric
from fin_automation.models.sources import ExtractedEvidence
from fin_automation.prompts.financial_analysis import (
    FINANCIAL_ANALYSIS_SYSTEM_PROMPT,
    build_financial_analysis_task,
)
from fin_automation.tools.financial_calculation import (
    FinancialCalculationTool,
)


class FinancialAnalysisAgent(ToolCallingAgent):
    """Select calculations and interpret validated results."""

    def __init__(self, model_to_use: Model) -> None:
        """Initialize the Financial Analysis Agent."""

        self._calculation_tool = FinancialCalculationTool()

        super().__init__(
            tools=[self._calculation_tool],
            model=model_to_use,
            instructions=FINANCIAL_ANALYSIS_SYSTEM_PROMPT,
            max_steps=4,
            name="financial_analysis_agent",
            description=(
                "Selects bounded financial calculations, calls "
                "deterministic Python tooling, and interprets "
                "validated results."
            ),
        )

    def analyze(
        self,
        evidence: list[ExtractedEvidence],
        workflow_id: UUID,
    ) -> tuple[list[CalculatedMetric], str]:
        """Analyze extracted evidence using deterministic calculations."""

        self._calculation_tool.begin_run(
            workflow_id=workflow_id,
            evidence=evidence,
        )

        task = build_financial_analysis_task(evidence)

        final_answer = str(
            self.run(
                task,
                reset=True,
            )
        )

        return (
            self._calculation_tool.accepted_calculations,
            final_answer,
        )