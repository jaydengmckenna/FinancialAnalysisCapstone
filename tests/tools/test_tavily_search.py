"""Tests for Tavily search input validation and response mapping."""

import json
from uuid import uuid4

from fin_automation.tools.tavily_search import TavilySearchTool


class FakeTavilyClient:
    """Minimal fake Tavily client for tool tests."""

    def search(self, **kwargs):
        return {
            "results": [
                {
                    "title": "Example company update",
                    "url": "https://example.com/news/example",
                    "content": "Example news snippet.",
                    "raw_content": "Raw content from the source page.",
                }
            ]
        }


def test_tavily_search_accepts_current_sdk_depths() -> None:
    """Current Tavily SDK depth values should be accepted by the tool."""

    tool = TavilySearchTool(api_key="test-key", client=FakeTavilyClient())

    payload = tool.forward(
        query="Example company financial outlook",
        workflow_id=str(uuid4()),
        query_id=str(uuid4()),
        search_depth="fast",
        max_results=1,
    )

    results = json.loads(payload)
    assert len(results) == 1
    assert results[0]["title"] == "Example company update"
    assert results[0]["domain"] == "example.com"
    assert results[0]["raw_content_available"] is True


class EmptyTavilyClient:
    """Fake Tavily client simulating a query with no relevant results."""

    def search(self, **kwargs):
        return {"results": []}


def test_tavily_search_returns_empty_list_for_no_results() -> None:
    """A query with no relevant results must return an empty result
    list rather than raising or fabricating a result."""

    tool = TavilySearchTool(api_key="test-key", client=EmptyTavilyClient())

    payload = tool.forward(
        query="An extremely obscure query with nothing relevant",
        workflow_id=str(uuid4()),
        query_id=str(uuid4()),
        search_depth="basic",
        max_results=5,
    )

    results = json.loads(payload)
    assert results == []
