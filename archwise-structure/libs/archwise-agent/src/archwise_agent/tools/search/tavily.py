"""Safe, bounded public-web search backed by Tavily."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Annotated, Any, Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator

from archwise_agent.config import settings

logger = logging.getLogger(__name__)

_MAX_QUERY_LENGTH = 500
_MAX_CONTENT_LENGTH = 4_000
_PRIVATE_QUERY_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]+-----", re.IGNORECASE),
    re.compile(r"(?i)(?:[a-z]:\\|\\\\|/(?:home|users|private|tmp|var)/)"),
    re.compile(r"(?i)\b(?:api[_ -]?key|secret|password|token)\s*[:=]"),
    re.compile(r"```"),
)
_PRIVATE_DOMAIN_SUFFIXES = (".internal", ".local", ".lan")


class TavilySearchInput(BaseModel):
    """Arguments accepted by the bounded public-web search tool."""

    query: str = Field(
        min_length=3,
        max_length=_MAX_QUERY_LENGTH,
        description=(
            "A concise public-web query using public technology names, versions, "
            "standards, advisories, or generic error messages. Never include "
            "source code, secrets, local paths, or private project context."
        ),
    )
    topic: Literal["general", "news", "finance"] = Field(
        default="general",
        description="Search category. Use news for recent announcements or advisories.",
    )
    search_depth: Literal["basic", "advanced"] = Field(
        default="basic",
        description="Use advanced only when a more thorough search is justified.",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=5,
        description="Maximum number of concise source results to return.",
    )
    include_domains: (
        list[Annotated[str, Field(min_length=1, max_length=253)]] | None
    ) = Field(
        default=None,
        max_length=5,
        description="Optional public domains to prioritize, without URL paths.",
    )
    exclude_domains: (
        list[Annotated[str, Field(min_length=1, max_length=253)]] | None
    ) = Field(
        default=None,
        max_length=5,
        description="Optional public domains to exclude, without URL paths.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        query = value.strip()
        if any(pattern.search(query) for pattern in _PRIVATE_QUERY_PATTERNS):
            raise ValueError(
                "Search queries must contain only safe public concepts; private "
                "code, secrets, and local paths are not allowed."
            )
        return query

    @field_validator("include_domains", "exclude_domains")
    @classmethod
    def validate_domains(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        for domain in value:
            normalized = domain.strip().lower()
            if (
                "://" in normalized
                or "/" in normalized
                or normalized.endswith(_PRIVATE_DOMAIN_SUFFIXES)
            ):
                raise ValueError(
                    "Domains must be public hostnames without paths or URL schemes."
                )
        return [domain.strip() for domain in value]


@lru_cache(maxsize=1)
def _tavily_client(api_key: str) -> Any:
    """Create the client lazily so Tavily remains optional at app startup."""

    try:
        from tavily import TavilyClient
    except ImportError as error:
        raise RuntimeError(
            "Tavily is not installed. Install the research extra with "
            "`uv sync --extra research`."
        ) from error
    return TavilyClient(api_key=api_key)


def _truncate(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _normalise_results(
    payload: dict[str, Any], max_results: int
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in payload.get("results", [])[:max_results]:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        score = item.get("score")
        results.append(
            {
                "title": _truncate(item.get("title"), 300),
                "url": url,
                "content": _truncate(item.get("content"), _MAX_CONTENT_LENGTH),
                "score": score if isinstance(score, (int, float)) else None,
                "published_date": item.get("published_date"),
            }
        )
    return results


def _unavailable(message: str) -> dict[str, Any]:
    return {"status": "unavailable", "results": [], "message": message}


@tool("tavily_search", args_schema=TavilySearchInput)
def tavily_search(
    query: str,
    topic: Literal["general", "news", "finance"] = "general",
    search_depth: Literal["basic", "advanced"] = "basic",
    max_results: int = 5,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Search the public web for current, authoritative external information.

    Use this only when local repository evidence is insufficient or the question
    depends on current external facts, such as official documentation, release
    notes, compatibility details, public issues, or security advisories. Search
    with safe public concepts only. Never send source code, file contents,
    private project details, local paths, credentials, or secrets. Prefer narrow
    queries and verify important claims against the returned source URLs.

    The result contains a status, an optional short answer, and concise source
    records with titles, URLs, excerpts, scores, and publication dates. It does
    not request or return raw page content.
    """

    if not settings.tavily_api_key:
        return _unavailable(
            "Tavily search is not configured. No external search was performed."
        )

    try:
        client = _tavily_client(settings.tavily_api_key)
    except RuntimeError as error:
        return _unavailable(str(error))

    search_kwargs: dict[str, Any] = {
        "query": query,
        "topic": topic,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": False,
    }
    if include_domains:
        search_kwargs["include_domains"] = include_domains
    if exclude_domains:
        search_kwargs["exclude_domains"] = exclude_domains

    try:
        payload = client.search(**search_kwargs)
    except Exception as error:  # noqa: BLE001 - provider failures become results.
        logger.warning("Tavily search failed (%s)", type(error).__name__)
        return _unavailable(
            "Tavily search failed. No reliable external result was returned."
        )

    return {
        "status": "ok",
        "query": query,
        "answer": _truncate(payload.get("answer"), _MAX_CONTENT_LENGTH),
        "results": _normalise_results(payload, max_results),
    }


__all__ = ["TavilySearchInput", "tavily_search"]
