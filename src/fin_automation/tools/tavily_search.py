"""Tavily web-search tool used by the Source Selection Agent."""

import json
from collections.abc import Mapping
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import AnyHttpUrl, ValidationError
from smolagents import Tool
from tavily import TavilyClient

from fin_automation.exceptions import ResearchError
from fin_automation.models.sources import SearchResult

MAX_RAW_CONTENT_CHARACTERS = 12_000

class TavilySearchTool(Tool):
    """Execute one approved research-plan query through Tavily."""

    name = "tavily_web_search"

    description = """
    Execute one approved SearchQuery from a validated ResearchPlan.

    Use only query text, workflow_id, and query_id values supplied in
    the research plan. Do not create a new query or modify an approved
    query.

    The tool returns a JSON array of validated SearchResult records.
    Each result preserves its workflow_id and query_id.
    """.strip()

    inputs = {
        "query": {
            "type": "string",
            "description": (
                "The exact approved query text from SearchQuery.query."
            ),
        },
        "workflow_id": {
            "type": "string",
            "description": (
                "The workflow UUID from the validated ResearchPlan."
            ),
        },
        "query_id": {
            "type": "string",
            "description": (
                "The UUID belonging to the approved SearchQuery."
            ),
        },
        "search_depth": {
            "type": "string",
            "description": (
                "Tavily search depth. Must be basic, advanced, fast, or "
                "ultra-fast."
            ),
        },
        "max_results": {
            "type": "integer",
            "description": (
                "Maximum search results to return. Must be between "
                "one and five."
            ),
        },
    }

    output_type = "string"

    def __init__(
        self,
        api_key: str,
        client: TavilyClient | None = None,
    ) -> None:
        """Initialize the Tavily search tool.

        Args:
            api_key: Tavily API key used when constructing the client.
            client: Optional Tavily client supplied for testing.

        Raises:
            ValueError: If no API key or injected client is supplied.
        """

        if client is None and not api_key.strip():
            raise ValueError(
                "A Tavily API key is required when no client is "
                "provided."
            )

        self._client = client or TavilyClient(
            api_key=api_key
        )

        self._results_by_id: dict[
            UUID,
            SearchResult,
        ] = {}

        super().__init__()


    def reset_results(self) -> None:
        """Clear results stored from previous agent runs."""

        self._results_by_id.clear()


    def get_result(
        self,
        search_result_id: UUID,
    ) -> SearchResult | None:
        """Return a stored SearchResult by identifier.

        Args:
            search_result_id: Identifier assigned to the Tavily result.

        Returns:
            The matching SearchResult, or None when the identifier was
            not returned during the current search operation.
        """

        return self._results_by_id.get(
            search_result_id
        )

    def forward(
        self,
        query: str,
        workflow_id: str,
        query_id: str,
        search_depth: Literal["basic", "advanced", "fast", "ultra-fast"],
        max_results: int,
    ) -> str:
        """Execute one approved Tavily search query.

        Args:
            query: Exact query text from the approved SearchQuery.
            workflow_id: Workflow UUID from the ResearchPlan.
            query_id: UUID of the approved SearchQuery.
            search_depth: Tavily depth, one of basic, advanced, fast, or
                ultra-fast.
            max_results: Maximum number of results from one through five.

        Returns:
            Lightweight SearchResult JSON for agent evaluation.

        Raises:
            ValueError: If any tool argument is invalid.
            ResearchError: If Tavily fails or returns an invalid response.
        """

        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError(
                "The approved search query cannot be empty."
            )

        if search_depth not in {
            "basic",
            "advanced",
            "fast",
            "ultra-fast",
        }:
            raise ValueError(
                "search_depth must be basic, advanced, fast, or ultra-fast."
            )

        if not 1 <= max_results <= 5:
            raise ValueError(
                "max_results must be between one and five."
            )

        try:
            parsed_workflow_id = UUID(
                workflow_id
            )
        except ValueError as error:
            raise ValueError(
                "workflow_id must be a valid UUID."
            ) from error

        try:
            parsed_query_id = UUID(
                query_id
            )
        except ValueError as error:
            raise ValueError(
                "query_id must be a valid UUID."
            ) from error

        try:
            raw_response = self._client.search(
                query=normalized_query,
                search_depth=search_depth,
                include_answer=False,
                include_raw_content=True,
                include_images=False,
                max_results=max_results,
            )
        except Exception as error:
            raise ResearchError(
                "Tavily search failed."
            ) from error

        search_results = self._map_response(
            raw_response=raw_response,
            workflow_id=parsed_workflow_id,
            query_id=parsed_query_id,
        )

        for search_result in search_results:
            self._results_by_id[
                search_result.search_result_id
            ] = search_result

        lightweight_results = [
            {
                "search_result_id": str(
                    search_result.search_result_id
                ),
                "workflow_id": str(
                    search_result.workflow_id
                ),
                "query_id": str(
                    search_result.query_id
                ),
                "title": search_result.title,
                "url": str(search_result.url),
                "snippet": search_result.snippet,
                "domain": search_result.domain,
                "result_position": (
                    search_result.result_position
                ),
                "raw_content_available": bool(
                    search_result.raw_content
                ),
                "raw_content_characters": len(
                    search_result.raw_content or ""
                ),
            }
            for search_result in search_results
        ]

        return json.dumps(
            lightweight_results,
            ensure_ascii=False,
        )
    @staticmethod
    def _map_response(
        raw_response: object,
        workflow_id: UUID,
        query_id: UUID,
    ) -> list:
        """Convert a Tavily response into SearchResult records.

        Args:
            raw_response: Response returned by Tavily search.
            workflow_id: Current workflow identifier.
            query_id: Identifier of the executed SearchQuery.

        Returns:
            Validated SearchResult records in provider result order.

        Raises:
            ResearchError: If the overall Tavily response is malformed.
        """

        if not isinstance(raw_response, Mapping):
            raise ResearchError(
                "Tavily returned an invalid search response."
            )

        raw_results = raw_response.get("results")

        if not isinstance(raw_results, list):
            raise ResearchError(
                "Tavily search response did not contain a results "
                "list."
            )

        search_results: list[SearchResult] = []

        for position, raw_result in enumerate(
            raw_results,
            start=1,
        ):
            if not isinstance(raw_result, Mapping):
                continue

            title = raw_result.get("title")
            url = raw_result.get("url")
            content = raw_result.get("content")
            raw_content = raw_result.get(
                "raw_content"
            )

            if not isinstance(title, str):
                continue

            normalized_title = title.strip()

            if not normalized_title:
                continue

            if not isinstance(url, str):
                continue

            normalized_url = url.strip()

            if not normalized_url:
                continue

            domain = (
                urlsplit(normalized_url)
                .netloc
                .casefold()
            )

            if not domain:
                continue

            snippet = (
                content.strip()
                if isinstance(content, str)
                and content.strip()
                else None
            )

            validated_raw_content = None

            if isinstance(raw_content, str):
                normalized_raw_content = (
                    raw_content.strip()
                )

                if normalized_raw_content:
                    validated_raw_content = (
                        normalized_raw_content[
                            :MAX_RAW_CONTENT_CHARACTERS
                        ]
                    )

            try:
                validated_url: AnyHttpUrl = AnyHttpUrl(normalized_url)
                search_result = SearchResult(
                    workflow_id=workflow_id,
                    query_id=query_id,
                    title=normalized_title,
                    url=validated_url,
                    snippet=snippet,
                    raw_content=validated_raw_content,
                    domain=domain,
                    result_position=position,
                )
            except (ValidationError, ValueError):
                continue

            search_results.append(
                search_result
            )

        return search_results




