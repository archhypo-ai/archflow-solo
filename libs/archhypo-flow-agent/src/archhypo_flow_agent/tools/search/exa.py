"""Bounded Exa public-web search, not automatically exposed to agents."""

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator

from archhypo_flow_agent.config.tool_config import get_key, is_available
from archhypo_flow_agent.tools.search.tavily import (
    TavilySearchInput,
    _normalise_results,
)


class ExaSearchInput(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=500,
        description="A safe public-web query; never include private data or secrets.",
    )
    max_results: int = Field(default=5, ge=1, le=5)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        return TavilySearchInput.validate_query(value)


@tool("exa_search", args_schema=ExaSearchInput)
def exa_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search public web sources with Exa; never send private data or secrets."""
    if not is_available("exa"):
        return {
            "status": "unavailable",
            "results": [],
            "message": "Exa is disabled or not configured.",
        }
    try:
        response = httpx.post(
            "https://api.exa.ai/search",
            headers={"x-api-key": get_key("exa")},
            json={
                "query": query,
                "numResults": max_results,
                "contents": {"text": {"maxCharacters": 4000}},
            },
            timeout=20.0,
            follow_redirects=False,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(
            payload.get("results"), list
        ):
            raise ValueError("Invalid Exa response")
        results = [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("text"),
                "score": item.get("score"),
                "published_date": item.get("publishedDate"),
            }
            for item in payload["results"]
            if isinstance(item, dict)
        ]
        return {
            "status": "ok",
            "query": query,
            "results": _normalise_results({"results": results}, max_results),
        }
    except (httpx.HTTPError, ValueError):
        return {"status": "unavailable", "results": [], "message": "Exa search failed."}
