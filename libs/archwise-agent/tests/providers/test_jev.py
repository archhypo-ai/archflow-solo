import httpx
import pytest

from archwise_agent.providers.jev import (
    JevDecisionClient,
    JevRequestError,
)


class FakeResponse:
    status_code = 200

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_jev_client_posts_generic_decision_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse(
            {
                "model": "typesafe/jev-1.13",
                "answers": {
                    "route": {
                        "type": "choice",
                        "choice": "archwise_workflow",
                        "confidence": 0.98,
                        "probabilities": {
                            "archwise_workflow": 0.99,
                            "direct_response": 0.01,
                        },
                    }
                },
            }
        )

    monkeypatch.setattr("archwise_agent.providers.jev.httpx.post", post)
    client = JevDecisionClient(
        api_key="secret",
        model="typesafe/jev-1.13",
        endpoint="https://example.test/api/alpha/decisions",
    )

    response = client.decide(
        state="Analyze this architectural uncertainty.",
        questions={"route": {"type": "choice"}},
    )

    assert captured["url"] == "https://example.test/api/alpha/decisions"
    assert captured["json"] == {
        "model": "typesafe/jev-1.13",
        "state": "Analyze this architectural uncertainty.",
        "questions": {"route": {"type": "choice"}},
    }
    assert response.answers["route"].choice == "archwise_workflow"
    assert response.answers["route"].confidence == 0.98


def test_jev_client_wraps_transport_timeouts(monkeypatch) -> None:
    def post(*args, **kwargs):
        request = httpx.Request("POST", "https://example.test")
        raise httpx.ReadTimeout("timed out", request=request)

    monkeypatch.setattr("archwise_agent.providers.jev.httpx.post", post)
    client = JevDecisionClient(
        api_key="secret",
        model="typesafe/jev-1.13",
        endpoint="https://example.test/api/alpha/decisions",
    )

    with pytest.raises(JevRequestError, match="Jev request failed"):
        client.decide(state="message", questions={"route": {"type": "choice"}})


def test_jev_client_wraps_http_errors(monkeypatch) -> None:
    def post(*args, **kwargs):
        request = httpx.Request("POST", "https://example.test")
        response = httpx.Response(503, request=request)
        raise httpx.HTTPStatusError("unavailable", request=request, response=response)

    monkeypatch.setattr("archwise_agent.providers.jev.httpx.post", post)
    client = JevDecisionClient(
        api_key="secret",
        model="typesafe/jev-1.13",
        endpoint="https://example.test/api/alpha/decisions",
    )

    with pytest.raises(JevRequestError, match="status=503"):
        client.decide(state="message", questions={"route": {"type": "choice"}})
