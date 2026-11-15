import httpx
import pytest
from pydantic import ValidationError

from archhypo_flow_agent.tools.search import exa


def test_exa_search_maps_results_and_sends_key(monkeypatch):
    monkeypatch.setattr(exa, "is_available", lambda _: True)
    monkeypatch.setattr(exa, "get_key", lambda _: "example-secret")
    request = httpx.Request("POST", "https://api.exa.ai/search")

    def post(url, **kwargs):
        assert kwargs["headers"]["x-api-key"] == "example-secret"
        assert kwargs["json"]["numResults"] == 3
        return httpx.Response(
            200,
            request=request,
            json={
                "results": [
                    {
                        "url": "https://example.org",
                        "title": "Result",
                        "text": "Excerpt",
                        "publishedDate": "2025-01-01",
                    }
                ]
            },
        )

    monkeypatch.setattr(exa.httpx, "post", post)
    result = exa.exa_search.invoke({"query": "public documentation", "max_results": 3})
    assert result["status"] == "ok"
    assert result["results"][0]["content"] == "Excerpt"
    assert "example-secret" not in str(result)


def test_exa_disabled_and_private_query(monkeypatch):
    monkeypatch.setattr(exa, "is_available", lambda _: False)
    assert (
        exa.exa_search.invoke({"query": "public documentation"})["status"]
        == "unavailable"
    )
    with pytest.raises(ValidationError):
        exa.exa_search.invoke({"query": "secret: my-private-value"})
