import httpx
import pytest
from pydantic import SecretStr

from archhypo_flow_agent.config import AgentSettings
from archhypo_flow_agent.providers.system_one import (
    OpenRouterSystemOneClient,
    SystemOneRequestError,
    SystemOneResponseError,
    create_system_one_client,
)


class FakeResponse:
    status_code = 200

    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


@pytest.mark.parametrize("model_name", ["typesafe/jev-1.13", "microsoft/example-model"])
def test_system_one_uses_configured_model_without_provider_specific_selection(
    monkeypatch,
    model_name: str,
) -> None:
    captured: dict[str, object] = {}

    def post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse(
            {
                "model": model_name,
                "answers": {
                    "route": {
                        "type": "choice",
                        "choice": "direct_response",
                        "confidence": 0.94,
                    }
                },
            }
        )

    monkeypatch.setattr("archhypo_flow_agent.providers.system_one.httpx.post", post)
    monkeypatch.setenv("SYSTEM_ONE_MODEL", model_name)
    monkeypatch.setenv("SYSTEM_ONE_ENDPOINT", "https://example.test/decisions")
    monkeypatch.setenv("SYSTEM_ONE_TIMEOUT", "12")
    configuration = AgentSettings(
        _env_file=None,
        openrouter_api_key=SecretStr("test-key"),
    )

    client = create_system_one_client(configuration)
    result = client.decide(
        state={"message": "Explain the current hypothesis."},
        questions={"route": {"type": "choice"}},
        session_id="conversation-1",
    )

    assert isinstance(client, OpenRouterSystemOneClient)
    assert captured["url"] == "https://example.test/decisions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["timeout"] == 12
    assert captured["json"] == {
        "model": model_name,
        "state": {"message": "Explain the current hypothesis."},
        "questions": {"route": {"type": "choice"}},
        "session_id": "conversation-1",
    }
    assert result.answers["route"].choice == "direct_response"


def test_system_one_requires_an_explicit_model(monkeypatch) -> None:
    monkeypatch.delenv("SYSTEM_ONE_MODEL", raising=False)
    configuration = AgentSettings(
        _env_file=None,
        openrouter_api_key=SecretStr("test-key"),
    )

    with pytest.raises(ValueError, match="SYSTEM_ONE_MODEL is required"):
        create_system_one_client(configuration)


def test_system_one_wraps_transport_and_invalid_response_errors(monkeypatch) -> None:
    configuration = AgentSettings(
        _env_file=None,
        openrouter_api_key=SecretStr("test-key"),
        system_one_model="provider/model",
    )
    client = create_system_one_client(configuration)

    def timeout(*_args, **_kwargs):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr("archhypo_flow_agent.providers.system_one.httpx.post", timeout)
    with pytest.raises(SystemOneRequestError, match="request failed"):
        client.decide(state="message", questions={"route": {"type": "choice"}})

    monkeypatch.setattr(
        "archhypo_flow_agent.providers.system_one.httpx.post",
        lambda *_args, **_kwargs: FakeResponse({"model": "provider/model"}),
    )
    with pytest.raises(SystemOneResponseError, match="invalid response"):
        client.decide(state="message", questions={"route": {"type": "choice"}})
