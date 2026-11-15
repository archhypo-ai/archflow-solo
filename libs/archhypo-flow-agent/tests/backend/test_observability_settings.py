import json

import keyring
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from archhypo_flow_agent.backend.controllers.providers import router
from archhypo_flow_agent.config import settings
from archhypo_flow_agent.config.provider_config import effective_provider_settings


def test_observability_settings_and_keyring(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(settings, "langsmith_tracing", True)
    monkeypatch.setattr(settings, "langsmith_api_key", SecretStr("environment"))
    monkeypatch.setattr(settings, "langfuse_enabled", False)
    monkeypatch.setattr(settings, "langfuse_public_key", None)
    monkeypatch.setattr(settings, "langfuse_secret_key", None)
    store = {}
    monkeypatch.setattr(keyring, "get_password", lambda service, name: store.get(name))
    monkeypatch.setattr(
        keyring,
        "set_password",
        lambda service, name, value: store.update({name: value}),
    )
    app = FastAPI()
    app.include_router(router)
    api = TestClient(app)
    original = {p["id"]: p for p in api.get("/api/providers/observability").json()}
    assert original["langsmith"]["enabled"] and original["langsmith"]["configured"]
    assert not original["langfuse"]["configured"]
    response = api.put(
        "/api/providers/observability/langfuse",
        json={
            "enabled": True,
            "public_key": "public-value",
            "secret_key": "secret-value",
        },
    )
    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert "secret-value" not in response.text
    assert "public-value" not in response.text
    api.put("/api/providers/observability/langsmith", json={"enabled": False})
    effective = effective_provider_settings()
    assert effective.langfuse_enabled is True
    assert effective.langfuse_secret_key.get_secret_value() == "secret-value"
    assert effective.langsmith_tracing is False
    assert effective.langsmith_api_key.get_secret_value() == "environment"
    persisted = (tmp_path / ".archhypoflow/providers.json").read_text()
    assert json.loads(persisted) == {
        "langfuse_enabled": True,
        "langsmith_tracing": False,
    }
    assert "secret-value" not in persisted and "public-value" not in persisted
    assert (
        api.put(
            "/api/providers/observability/langsmith",
            json={"enabled": True, "secret_key": "bad"},
        ).status_code
        == 400
    )
