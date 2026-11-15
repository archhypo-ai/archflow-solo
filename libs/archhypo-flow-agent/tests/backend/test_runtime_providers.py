import importlib

from fastapi.testclient import TestClient
from pydantic import SecretStr

from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.config import AgentSettings
from archhypo_flow_agent.services import AgentService
from tests.fakes import StubSystemOneClient, stub_chat_model

service_module = importlib.import_module("archhypo_flow_agent.services.agent_service")


def test_health_and_chat_recover_after_initial_configuration(tmp_path, monkeypatch):
    config = [
        AgentSettings(_env_file=None, openrouter_api_key=None, system_one_model=None)
    ]
    monkeypatch.setattr(
        service_module,
        "create_openrouter_model",
        lambda value: stub_chat_model("ready"),
    )
    monkeypatch.setattr(
        service_module,
        "create_system_one_client",
        lambda value: StubSystemOneClient("contextual_question", "contextual_question"),
    )
    service = AgentService(
        database_path=tmp_path / "runtime.sqlite",
        tools=[],
        provider_settings_resolver=lambda: config[0],
    )
    try:
        with TestClient(create_app(service)) as api:
            assert api.get("/health").json()["agent_ready"] is False
            assert (
                api.post(
                    "/api/chat", json={"thread_id": "a", "message": "hello"}
                ).status_code
                == 503
            )
            config[0] = AgentSettings(
                _env_file=None,
                openrouter_api_key=SecretStr("key"),
                system_one_model="vendor/decision",
            )
            assert api.get("/health").json()["agent_ready"] is True
            response = api.post(
                "/api/chat", json={"thread_id": "a", "message": "hello"}
            )
            assert response.status_code == 200
            assert response.json()["message"] == "ready"
            stream = api.post(
                "/api/chat/stream", json={"thread_id": "b", "message": "hello again"}
            )
            assert stream.status_code == 200
            assert '"type": "conversation_started"' in stream.text
            assert '"type": "done"' in stream.text
    finally:
        service.close()
