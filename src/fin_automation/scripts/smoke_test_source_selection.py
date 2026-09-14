"""Live smoke test for Tavily search and source selection."""

from uuid import uuid4

from smolagents import OpenAIServerModel

from fin_automation.agents.source_selection import (
    SourceSelectionAgent,
)
from fin_automation.config import get_settings
from fin_automation.models.common import (
    SearchPurpose,
    SourceCategory,
)
from fin_automation.models.research import (
    EvidenceRequirement,
    ResearchPlan,
    SearchQuery,
)
from fin_automation.tools.tavily_search import (
    TavilySearchTool,
)


def create_smoke_test_plan() -> ResearchPlan:
    """Create one small research plan for the live smoke test."""

    workflow_id = uuid4()

    evidence_requirement = EvidenceRequirement(
        name="Microsoft revenue growth",
        description=(
            "Find recent primary-source evidence about Microsoft's "
            "reported annual revenue growth."
        ),
        candidate_name="Microsoft",
        search_purpose=SearchPurpose.FINANCIAL_GROWTH,
        preferred_source_categories=[
            SourceCategory.PRIMARY,
            SourceCategory.SECONDARY,
        ],
        required=True,
    )

    search_query = SearchQuery(
        query=(
            "Microsoft annual revenue growth 2025 "
            "investor relations"
        ),
        purpose=SearchPurpose.FINANCIAL_GROWTH,
        candidate_name="Microsoft",
        evidence_requirement_ids=[
            evidence_requirement.requirement_id
        ],
    )

    return ResearchPlan(
        workflow_id=workflow_id,
        research_objective=(
            "Locate recent public evidence about Microsoft's "
            "reported annual revenue growth."
        ),
        candidate_discovery_required=False,
        candidate_names=["Microsoft"],
        comparison_criteria=[
            "revenue growth",
        ],
        risk_categories=[
            "revenue-growth sustainability",
        ],
        evidence_requirements=[
            evidence_requirement,
        ],
        search_queries=[
            search_query,
        ],
        preferred_source_categories=[
            SourceCategory.PRIMARY,
            SourceCategory.SECONDARY,
        ],
        candidate_limit=1,
        source_limit_per_candidate=3,
        assumptions=[],
    )


def main() -> None:
    """Execute the live Phase 5B source-selection smoke test."""

    settings = get_settings()

    research_plan = create_smoke_test_plan()

    model = OpenAIServerModel(
        model_id=settings.model_id,
        api_key=(
            settings.openai_api_key.get_secret_value()
        ),
        api_base=str(settings.openai_base_url),
    )

    tavily_search_tool = TavilySearchTool(
        api_key=(
            settings.tavily_api_key.get_secret_value()
        )
    )

    source_selection_agent = SourceSelectionAgent(
        model_to_use=model,
        tavily_search_tool=tavily_search_tool,
    )

    print("Running the live source-selection smoke test...")
    print(f"Workflow ID: {research_plan.workflow_id}")
    print(f"Plan ID: {research_plan.plan_id}")
    print(
        "Approved query: "
        f"{research_plan.search_queries[0].query}"
    )

    source_selection = (
        source_selection_agent.search_and_select(
            research_plan=research_plan
        )
    )

    selected_sources = [
        selection
        for selection in source_selection.selections
        if selection.selected
    ]

    excluded_sources = [
        selection
        for selection in source_selection.selections
        if not selection.selected
    ]

    print()
    print("Smoke test completed successfully.")
    print(f"Status: {source_selection.status.value}")
    print(
        "Reviewed results: "
        f"{len(source_selection.selections)}"
    )
    print(
        f"Selected results: {len(selected_sources)}"
    )
    print(
        f"Excluded results: {len(excluded_sources)}"
    )
    print(
        "Uncovered requirements: "
        f"{source_selection.uncovered_evidence_requirement_ids}"
    )
    print(
        "Uncovered requirements: "
        f"{len(source_selection.uncovered_evidence_requirement_ids)}"
    )

    if selected_sources:
        print()
        print("Selected source records:")

        for selection in selected_sources:
            print(
                "- Search result ID: "
                f"{selection.search_result_id}"
            )
            print(
                f"  Title: {selection.title}"
            )
            print(
                f"  URL: {selection.url}"
            )
            print(
                f"  Domain: {selection.domain}"
            )
            print(
                "  Raw content characters: "
                f"{len(selection.raw_content or '')}"
            )
            print(
                "  Candidate: "
                f"{selection.candidate_name or 'Not assigned'}"
            )
            print(
                "  Expected category: "
                f"{selection.expected_source_category.value}"
            )
            print(
                f"  Reason: {selection.selection_reason}"
            )

    if excluded_sources:
        print()
        print("Excluded source records:")

        for selection in excluded_sources:
            print(
                "- Search result ID: "
                f"{selection.search_result_id}"
            )
            print(
                "  Candidate: "
                f"{selection.candidate_name or 'Not assigned'}"
            )
            print(
                f"  Reason: {selection.selection_reason}"
            )
            print(
                "  Exclusion reason: "
                f"{selection.exclusion_reason}"
            )

    if source_selection.uncovered_evidence_requirement_ids:
        print()
        print("Uncovered evidence requirements:")

        for requirement_id in (
            source_selection.uncovered_evidence_requirement_ids
        ):
            print(f"- {requirement_id}")

    if source_selection.additional_research_requests:
        print()
        print("Additional research requests:")

        for request in (
            source_selection.additional_research_requests
        ):
            print(f"- Missing evidence: {request.missing_evidence}")
            print(f"  Reason: {request.reason}")
            print(
                "  Search purpose: "
                f"{request.suggested_search_purpose.value}"
            )
            

if __name__ == "__main__":
    main()
