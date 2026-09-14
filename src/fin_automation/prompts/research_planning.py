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
11. Give every evidence requirement a unique identifier.
12. Create search queries that support the approved evidence
    requirements.
13. Give every search query a unique identifier.
14. Ensure every search query references at least one evidence
    requirement.
15. Ensure each search query has the same search purpose as at least
    one evidence requirement it references.
16. Prefer primary sources for directly reported company financial
    information.
17. Prefer reputable secondary sources for independent context or
    corroboration.
18. Do not prefer unsupported source categories.
19. Include both favorable and unfavorable research areas.
20. Include material risks that could weaken a candidate.
21. Do not invent investor preferences, exclusions, constraints,
    financial values, sources, evidence, calculations, rankings, or
    recommendations.
22. Record necessary planning assumptions explicitly.
23. Do not resolve missing material information through a silent
    assumption.
24. Use only the supported SearchPurpose values supplied by the output
    schema.
25. Use only the supported SourceCategory values supplied by the output
    schema.
26. Return a ResearchPlan for the same workflow as the validated
    intake.
27. Return the final answer as one JSON object only.
28. Do not wrap the JSON object in Markdown code fences.
29. Do not provide explanations before or after the JSON object.
30. Return only data conforming to the required ResearchPlan schema.

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