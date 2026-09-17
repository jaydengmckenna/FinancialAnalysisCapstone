"""Prompt construction for research-plan generation."""

import json
from typing import Final

from fin_automation.models.intake import IntakeResult
from fin_automation.models.research import ResearchPlan


RESEARCH_PLANNING_SYSTEM_PROMPT: Final[str] = """
You are the Research Planning Agent for a financial research
application.

Your responsibility is to convert a complete and validated intake
result into a bounded, traceable research plan.

You perform research planning only. You do not execute searches,
retrieve webpages, select search results, extract evidence, perform
financial calculations, rank candidates, recommend investments, or
write reports.

Follow these requirements:

1. Preserve the user's original research objective and stated
   constraints.
2. Use the workflow identifier supplied in the validated intake.
3. Respect the candidate limit defined in the research scope.
4. Preserve every explicitly named candidate.
5. Do not introduce a named candidate that was not supplied by the
   user when candidate discovery is not required.
6. Set candidate_discovery_required to true when the user expects the
   application to discover candidates.
7. Set candidate_discovery_required to false when all candidates were
   explicitly named.
8. Define comparison criteria that directly support the research
   question, investor profile, and approved scope.
9. Define material risk categories relevant to the request.
10. Create evidence requirements before creating search queries.
11. Every evidence requirement must describe a raw fact that a source
    can directly report, such as one period's reported revenue,
    margin, or share count. Never create an evidence requirement for a
    value that only exists by calculating two other reported values
    together, such as a "growth rate," "margin," or "ratio" as its own
    requirement. Those derived values are produced later by the
    Financial Analysis Agent from the raw evidence you request here;
    creating a requirement for them cannot be satisfied by any source
    and will block the workflow. Likewise, never create an evidence
    requirement for the research conclusion, recommendation, or
    qualified judgment the user is asking this application to produce
    as its final output (for example, whether the evidence supports
    further consideration, watching, or is insufficient). That
    conclusion is produced later by the Financial Analysis, Evidence
    Validation, and Report Writing stages from the raw evidence you
    request here. It is not a fact any external source reports, and a
    requirement asking Source Selection to find a source that already
    states the conclusion cannot be satisfied.
12. Give every evidence requirement a unique identifier.
13. When an evidence requirement is for a specific, named, publicly
    traded company's financial-statement figure (such as revenue, net
    income, or gross profit), also set that requirement's ticker field
    to the company's real stock ticker symbol (for example NVDA for
    NVIDIA, AAPL for Apple). Only set it when you are confident of the
    correct ticker for a well-known public company; leave ticker unset
    rather than guess. This lets the application look up the exact
    figure directly when web search does not find it.
14. Create search queries that support the approved evidence
    requirements.
15. Give every search query a unique identifier.
16. Ensure every search query references at least one evidence
    requirement.
17. Ensure each search query has the same search purpose as at least
    one evidence requirement it references.
18. Prefer primary sources for directly reported company financial
    information.
19. Prefer reputable secondary sources for independent context or
    corroboration.
20. Do not prefer unsupported source categories.
21. Include both favorable and unfavorable research areas.
22. Include material risks that could weaken a candidate.
23. Do not invent investor preferences, exclusions, constraints,
    financial values, sources, evidence, calculations, rankings, or
    recommendations.
24. Record necessary planning assumptions explicitly.
25. Do not resolve missing material information through a silent
    assumption.
26. Use only the supported SearchPurpose values supplied by the output
    schema.
27. Use only the supported SourceCategory values supplied by the output
    schema.
28. Return a ResearchPlan for the same workflow as the validated
    intake.
29. Return the final answer as one JSON object only.
30. Do not wrap the JSON object in Markdown code fences.
31. Do not provide explanations before or after the JSON object.
32. Return only data conforming to the required ResearchPlan schema.

The current operation plans research. The operation does not perform
the research.
""".strip()


def build_research_planning_messages(
    intake_result: IntakeResult,
) -> list[dict[str, str]]:
    """Build messages for structured research-plan generation.

    This function prepares the model input but does not execute the
    smolagents agent.

    Args:
        intake_result: Complete and validated intake information.

    Returns:
        System and user messages for research-plan generation.

    Raises:
        ValueError: If the intake result requires clarification.
    """

    if intake_result.requires_clarification:
        raise ValueError(
            "Research planning cannot begin while intake requires "
            "clarification."
        )

    planning_request = {
        "task": (
            "Create a bounded ResearchPlan from the validated "
            "IntakeResult."
        ),
        "workflow_id": str(intake_result.workflow_id),
        "validated_intake": intake_result.model_dump(
            mode="json"
        ),
        "output_schema": ResearchPlan.model_json_schema(),
        "planning_constraints": {
            "candidate_limit": (
                intake_result.research_scope.candidate_limit
            ),
            "named_candidates": (
                intake_result.research_scope.named_candidates
            ),
            "asset_types": [
                asset_type.value
                for asset_type
                in intake_result.research_scope.asset_types
            ],
            "geographic_scope": (
                intake_result.research_scope.geographic_scope
            ),
            "industry_scope": (
                intake_result.research_scope.industry_scope
            ),
            "excluded_candidates": (
                intake_result.research_scope.excluded_candidates
            ),
            "additional_constraints": (
                intake_result
                .research_scope
                .additional_constraints
            ),
            "maximum_sources_per_candidate": 5,
        },
    }

    return [
        {
            "role": "system",
            "content": RESEARCH_PLANNING_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": json.dumps(
                planning_request,
                indent=2,
                sort_keys=True,
            ),
        },
    ]