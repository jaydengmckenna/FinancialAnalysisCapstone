"""Bounded live smoke test for Phase 6.

Adapt the model import/constructor below only if the project already has a
shared smolagents model factory. The financial-analysis implementation itself
requires no OpenAI SDK abstraction.
"""

import os
from decimal import Decimal
from uuid import uuid4

from smolagents import OpenAIServerModel

from fin_automation.agents.financial_analysis import FinancialAnalysisAgent
from fin_automation.models.sources import ExtractedEvidence


def main() -> None:
    workflow_id = uuid4()
    current = ExtractedEvidence(
        workflow_id=workflow_id,
        source_id=uuid4(),
        candidate_name="Microsoft",
        evidence_type="revenue",
        content="For FY2025, Microsoft reported revenue of $281.7 billion.",
        reported_value=Decimal("281.7"),
        currency="USD",
        unit="billion",
        reporting_period="FY2025",
    )
    previous = ExtractedEvidence(
        workflow_id=workflow_id,
        source_id=uuid4(),
        candidate_name="Microsoft",
        evidence_type="revenue",
        content="For FY2024, Microsoft reported revenue of $245.1 billion.",
        reported_value=Decimal("245.1"),
        currency="USD",
        unit="billion",
        reporting_period="FY2024",
    )
    model = OpenAIServerModel(
        model_id=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        api_key=os.environ["OPENAI_API_KEY"],
    )
    agent = FinancialAnalysisAgent(model)
    calculations, interpretation = agent.analyze(
        evidence=[current, previous],
        workflow_id=workflow_id,
    )
    if not calculations:
        raise RuntimeError("Smoke test produced no validated calculation.")
    print("Phase 6 smoke test completed successfully.")
    print(calculations[0].model_dump_json(indent=2))
    print(interpretation)


if __name__ == "__main__":
    main()
