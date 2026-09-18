import importlib

import pytest
from pydantic import ValidationError

from archwise_agent.config import settings
from archwise_agent.tools.search import tavily_search

tavily_module = importlib.import_module("archwise_agent.tools.search.tavily")


def test_tavily_search_reports_when_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "tavily_api_key", "")

    result = tavily_search.invoke({"query": "Python release notes"})

    assert result["status"] == "unavailable"
    assert result["results"] == []
    assert "No external search was performed" in result["message"]


def test_tavily_search_rejects_private_query() -> None:
    with pytest.raises(ValidationError, match="private code"):
        tavily_search.invoke({"query": "api_key=do-not-send-this"})


def test_tavily_search_returns_bounded_source_records(monkeypatch) -> None:
    class FakeClient:
        def search(self, **kwargs):
            assert kwargs == {
                "query": "Python release notes",
                "topic": "general",
                "search_depth": "advanced",
                "max_results": 1,
                "include_answer": True,
                "include_raw_content": False,
                "include_domains": ["python.org"],
            }
            return {
                "answer": "A" * 5_000,
                "results": [
                    {
                        "title": "Python",
                        "url": "https://python.org/news",
                        "content": "B" * 5_000,
                        "raw_content": "private page dump that must not be returned",
                        "score": 0.9,
                        "published_date": "2026-01-01",
                    }
                ],
            }

    monkeypatch.setattr(settings, "tavily_api_key", "test-key")
    monkeypatch.setattr(tavily_module, "_tavily_client", lambda _: FakeClient())

    result = tavily_search.invoke(
        {
            "query": "Python release notes",
            "search_depth": "advanced",
            "max_results": 1,
            "include_domains": ["python.org"],
        }
    )

    assert result["status"] == "ok"
    assert len(result["answer"]) == 4_000
    assert result["results"] == [
        {
            "title": "Python",
            "url": "https://python.org/news",
            "content": "B" * 3_999 + "…",
            "score": 0.9,
            "published_date": "2026-01-01",
        }
    ]
    assert "raw_content" not in result["results"][0]
