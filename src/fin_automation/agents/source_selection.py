"""Source Selection Agent implementation using smolagents."""

from smolagents import Model, ToolCallingAgent

from fin_automation.models.common import (
    SourceSelectionStatus,
)
from fin_automation.models.research import (
    AdditionalResearchRequest,
    ResearchPlan,
)
from fin_automation.models.sources import (
    SourceSelection,
)
from fin_automation.prompts.source_selection import (
    SOURCE_SELECTION_SYSTEM_PROMPT,
    build_source_selection_messages,
)
from fin_automation.tools.source_selection_submission import (
    SubmitSourceSelectionTool,
)
from fin_automation.tools.tavily_search import (
    TavilySearchTool,
)


class SourceSelectionAgent(ToolCallingAgent):
    """Search for and select sources from an approved ResearchPlan."""

    def __init__(
        self,
        model_to_use: Model,
        tavily_search_tool: TavilySearchTool,
    ) -> None:
        """Initialize the Source Selection Agent.

        Args:
            model_to_use: A smolagents-compatible model.
            tavily_search_tool: Configured Tavily search tool.
        """

        self._tavily_search_tool = (
            tavily_search_tool
        )

        self._submission_tool = (
            SubmitSourceSelectionTool(
                tavily_search_tool=(
                    self._tavily_search_tool
                )
            )
        )

        super().__init__(
            tools=[
                self._tavily_search_tool,
                self._submission_tool,
            ],
            model=model_to_use,
            instructions=(
                SOURCE_SELECTION_SYSTEM_PROMPT
            ),
            max_steps=12,
            name="source_selection_agent",
            description=(
                "Executes approved financial-research queries and "
                "selects public sources for downstream analysis."
            ),
        )

    def search_and_select(
        self,
        research_plan: ResearchPlan,
        additional_research_requests: list[AdditionalResearchRequest] | None = None,
    ) -> SourceSelection:
        """Execute approved searches and select relevant sources.

        Args:
            research_plan: Validated plan containing evidence
                requirements and approved search queries.

        Returns:
            A validated SourceSelection containing selected source
            metadata and raw Tavily content.

        Raises:
            ValueError: If the agent does not submit a selection or
                the selection conflicts with the ResearchPlan.
        """

        self._tavily_search_tool.reset_results()
        self._submission_tool.reset()

        messages = build_source_selection_messages(
            research_plan=research_plan,
            additional_research_requests=additional_research_requests,
        )

        task = messages[1]["content"]

        self.run(
            task,
            reset=True,
        )

        source_selection = (
            self._submission_tool.last_selection
        )

        if source_selection is None:
            raise ValueError(
                "The Source Selection Agent completed without calling "
                "submit_source_selection."
            )

        self._validate_source_selection_identity(
            source_selection=source_selection,
            research_plan=research_plan,
        )

        return source_selection

    @staticmethod
    def _validate_source_selection_identity(
        source_selection: SourceSelection,
        research_plan: ResearchPlan,
    ) -> None:
        """Validate source selection against its ResearchPlan.

        Args:
            source_selection: Selection submitted by the agent.
            research_plan: Plan that initiated source selection.

        Raises:
            ValueError: If workflow, plan, evidence, candidate, or
                status information is inconsistent.
        """

        if (
            source_selection.workflow_id
            != research_plan.workflow_id
        ):
            raise ValueError(
                "The source selection workflow_id does not match "
                "the research plan."
            )

        if (
            source_selection.plan_id
            != research_plan.plan_id
        ):
            raise ValueError(
                "The source selection plan_id does not match the "
                "research plan."
            )

        known_requirement_ids = {
            requirement.requirement_id
            for requirement
            in research_plan.evidence_requirements
        }

        known_candidates = {
            candidate.casefold()
            for candidate
            in research_plan.candidate_names
        }

        for selection in source_selection.selections:
            unknown_requirement_ids = (
                set(
                    selection
                    .evidence_requirement_ids
                )
                - known_requirement_ids
            )

            if unknown_requirement_ids:
                raise ValueError(
                    "A selected source references an evidence "
                    "requirement outside the research plan."
                )

            if (
                selection.candidate_name is not None
                and not research_plan
                .candidate_discovery_required
                and selection.candidate_name
                .casefold()
                not in known_candidates
            ):
                raise ValueError(
                    "A source selection references a candidate "
                    "outside the research plan."
                )

            if (
                selection.selected
                and not selection.raw_content
            ):
                raise ValueError(
                    "A selected source does not contain Tavily raw "
                    "content for downstream analysis."
                )

        unknown_uncovered_ids = (
            set(
                source_selection
                .uncovered_evidence_requirement_ids
            )
            - known_requirement_ids
        )

        if unknown_uncovered_ids:
            raise ValueError(
                "The source selection contains an uncovered evidence "
                "requirement outside the research plan."
            )

        if (
            source_selection.status
            == SourceSelectionStatus
            .READY_FOR_RETRIEVAL
            and source_selection
            .uncovered_evidence_requirement_ids
        ):
            raise ValueError(
                "A ready-for-retrieval source selection cannot "
                "contain uncovered evidence requirements."
            )

        if (
            source_selection.status
            == SourceSelectionStatus
            .ADDITIONAL_SEARCH_REQUIRED
            and not source_selection
            .uncovered_evidence_requirement_ids
        ):
            raise ValueError(
                "An additional-search outcome must identify at least "
                "one uncovered evidence requirement."
            )

        for request in (
            source_selection
            .additional_research_requests
        ):
            requirement_id = (
                request.evidence_requirement_id
            )

            if (
                requirement_id is not None
                and requirement_id
                not in known_requirement_ids
            ):
                raise ValueError(
                    "An additional research request references an "
                    "evidence requirement outside the research plan."
                )