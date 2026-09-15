"""Prompt construction for minimal Phase 6 financial analysis."""

import json

from fin_automation.models.sources import ExtractedEvidence


FINANCIAL_ANALYSIS_SYSTEM_PROMPT = """
You are a bounded Financial Analysis Agent.

Use only the validated extracted evidence supplied in the task.

You may call the financial calculation tool using one of these operations:

- growth_rate
- margin
- ratio
- difference

Use growth_rate when comparing a current value with a previous value.
The first evidence record must be the current value, and the second must
be the previous value.

Use margin when dividing a profit value by a revenue value.
The first evidence record must be the numerator, and the second must be
the denominator.

Use ratio when dividing one financial value by another.
The first evidence record must be the numerator, and the second must be
the denominator.

Use difference when directly comparing compatible values.
The calculation subtracts the second value from the first value.

Use evidence_id values when calling the calculation tool.

Never perform arithmetic yourself. All arithmetic must be performed by
the financial calculation tool.

Do not:

- Invent missing values.
- Use evidence outside the supplied task.
- Convert currencies.
- Convert incompatible units.
- Forecast future performance.
- Calculate company valuations.
- Create weighted scores.
- Rank candidates.
- Make investment decisions or recommendations.

If the evidence is missing, nonnumeric, or incompatible, explain the
limitation and do not call the calculation tool.

After a successful calculation, provide a concise factual interpretation.
Clearly separate the calculated result from interpretation and preserve
any relevant limitations.
""".strip()


def build_financial_analysis_task(
    evidence: list[ExtractedEvidence],
) -> str:
    """Build the bounded financial-analysis task."""

    if not evidence:
        raise ValueError(
            "Financial analysis requires extracted evidence."
        )

    evidence_payload = [
        record.model_dump(mode="json")
        for record in evidence
    ]

    return (
        "Analyze the validated extracted evidence below.\n\n"
        "Select one supported and meaningful calculation when the "
        "evidence permits it. Use the exact evidence_id values in the "
        "tool call.\n\n"
        "If no supported calculation can be completed, explain the "
        "specific limitation without inventing missing information.\n\n"
        "VALIDATED_EXTRACTED_EVIDENCE:\n"
        f"{json.dumps(evidence_payload, indent=2)}"
    )