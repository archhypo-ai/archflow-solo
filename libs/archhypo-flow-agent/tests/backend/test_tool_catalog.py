import json

import keyring
from fastapi import FastAPI
from fastapi.testclient import TestClient
from keyring.errors import KeyringError

from archhypo_flow_agent.backend.controllers.tool_catalog import router
from archhypo_flow_agent.config import settings


def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_credentials_and_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(settings, "tavily_api_key", None)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    store = {}
    monkeypatch.setattr(keyring, "get_password", lambda service, name: store.get(name))
    monkeypatch.setattr(
        keyring,
        "set_password",
        lambda service, name, value: store.update({name: value}),
    )
    api = client()
    tools = api.get("/api/tool-catalog").json()
    assert all(not tool["configured"] for tool in tools)
    assert {tool["id"]: tool["api_key_env"] for tool in tools} == {
        "tavily": "TAVILY_API_KEY",
        "exa": "EXA_API_KEY",
    }
    monkeypatch.setenv("EXA_API_KEY", "env-secret")
    assert api.get("/api/tool-catalog/exa").json()["configured"] is True
    monkeypatch.delenv("EXA_API_KEY")
    response = api.put(
        "/api/tool-catalog/tavily", json={"enabled": True, "api_key": "my-secret"}
    )
    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert "my-secret" not in response.text
    path = tmp_path / ".archhypoflow/tools/tavily.json"
    assert json.loads(path.read_text()) == {"enabled": True}
    assert "my-secret" not in path.read_text()
    assert store["tavily"] == "my-secret"
    assert (
        api.put("/api/tool-catalog/tavily", json={"enabled": False}).json()["enabled"]
        is False
    )
    assert store["tavily"] == "my-secret"
    assert api.get("/api/tool-catalog/tavily").json()["configured"] is True


def test_keyring_failure_and_symlinks(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(keyring, "get_password", lambda *args: None)

    def fail(*args):
        raise KeyringError("unavailable")

    monkeypatch.setattr(keyring, "set_password", fail)
    api = client()
    response = api.put(
        "/api/tool-catalog/exa", json={"enabled": True, "api_key": "secret"}
    )
    assert response.status_code == 503
    assert "secret" not in response.text
    root = tmp_path / ".archhypoflow"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "tools").symlink_to(outside, target_is_directory=True)
    assert api.put("/api/tool-catalog/exa", json={"enabled": True}).status_code == 500
    assert list(outside.iterdir()) == []
