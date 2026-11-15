import importlib

from fastapi.testclient import TestClient
from pydantic import SecretStr

from archhypo_flow_agent.config import AgentSettings


def test_saved_provider_settings_are_used_at_startup(monkeypatch):
    app = importlib.import_module("archhypo_flow_agent.backend.app")
    config = AgentSettings(
        _env_file=None,
        openrouter_api_key=SecretStr("key"),
        openrouter_model="vendor/chat",
        system_one_model="vendor/jev",
    )
    seen = {}
    monkeypatch.setattr(app, "effective_provider_settings", lambda: config)
    monkeypatch.setattr(
        app,
        "create_openrouter_model",
        lambda value: seen.setdefault("chat_config", value),
    )
    monkeypatch.setattr(
        app,
        "create_system_one_client",
        lambda value: seen.setdefault("system_config", value),
    )

    class Service:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        def close(self):
            pass

    monkeypatch.setattr(app, "AgentService", Service)
    with TestClient(app.create_app()):
        assert seen["chat_config"] is config
        assert seen["system_config"] is config
        assert seen["chat_model_id"] == "vendor/chat"
        assert seen["system_one_model_id"] == "vendor/jev"
