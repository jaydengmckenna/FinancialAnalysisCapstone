"""Live smoke test for Phase 5C evidence extraction."""

from smolagents import OpenAIServerModel

from fin_automation.agents.evidence_extraction import (
    EvidenceExtractionAgent,
)
from fin_automation.agents.source_selection import SourceSelectionAgent
from fin_automation.config import get_settings
from fin_automation.scripts.smoke_test_source_selection import (
    create_smoke_test_plan,
)
from fin_automation.tools.tavily_search import TavilySearchTool


def main() -> None:
    """Run source selection and extract evidence from one source."""

    settings = get_settings()
    research_plan = create_smoke_test_plan()

    model = OpenAIServerModel(
        model_id=settings.model_id,
        api_key=settings.openai_api_key.get_secret_value(),
        api_base=str(settings.openai_base_url),
    )

    tavily_tool = TavilySearchTool(
        api_key=settings.tavily_api_key.get_secret_value()
    )

    source_agent = SourceSelectionAgent(
        model_to_use=model,
        tavily_search_tool=tavily_tool,
    )

    source_selection = source_agent.search_and_select(research_plan)

    selected_sources = [
        source
        for source in source_selection.selections
        if source.selected and source.raw_content
    ]

    if not selected_sources:
        raise RuntimeError(
            "The smoke test did not produce a selected source with content."
        )

    selected_source = selected_sources[0]
    requirement_ids = set(selected_source.evidence_requirement_ids)
    requirements = [
        requirement
        for requirement in research_plan.evidence_requirements
        if requirement.requirement_id in requirement_ids
    ]

    evidence_agent = EvidenceExtractionAgent(model_to_use=model)
    source_record, evidence_records, evidence_gaps = (
        evidence_agent.extract_evidence(
            selected_source=selected_source,
            evidence_requirements=requirements,
            workflow_id=research_plan.workflow_id,
        )
    )

    print("Phase 5C smoke test completed successfully.")
    print(f"Source ID: {source_record.source_id}")
    print(f"Source title: {source_record.title}")
    print(f"Source URL: {source_record.url}")
    print(f"Evidence records: {len(evidence_records)}")
    print(f"Evidence gaps: {len(evidence_gaps)}")

    for evidence in evidence_records:
        print()
        print(f"Evidence ID: {evidence.evidence_id}")
        print(f"Type: {evidence.evidence_type}")
        print(f"Candidate: {evidence.candidate_name}")
        print(f"Content: {evidence.content[:300]}")
        print(f"Reported value: {evidence.reported_value}")
        print(f"Currency: {evidence.currency}")
        print(f"Unit: {evidence.unit}")
        print(f"Reporting period: {evidence.reporting_period}")

    if evidence_gaps:
        print()
        print("Evidence gaps:")
        for gap in evidence_gaps:
            print(f"- {gap}")


if __name__ == "__main__":
    main()
