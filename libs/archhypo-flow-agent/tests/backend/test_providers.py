import json

import httpx
import keyring
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from archhypo_flow_agent.backend.controllers.providers import router
from archhypo_flow_agent.config import settings
from archhypo_flow_agent.config.provider_config import effective_provider_settings


def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_provider_settings_keyring_and_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(settings, "openrouter_api_key", SecretStr("environment-key"))
    store = {}
    monkeypatch.setattr(keyring, "get_password", lambda service, name: store.get(name))
    monkeypatch.setattr(
        keyring,
        "set_password",
        lambda service, name, value: store.update({name: value}),
    )
    api = client()
    assert api.get("/api/providers/openrouter").json()["configured"] is True
    response = api.put(
        "/api/providers/openrouter",
        json={
            "openrouter_model": "vendor/chat",
            "system_one_model": "vendor/jev",
            "api_key": "saved-secret",
        },
    )
    assert response.status_code == 200
    assert "saved-secret" not in response.text
    path = tmp_path / ".archhypoflow/providers.json"
    assert json.loads(path.read_text()) == {
        "openrouter_model": "vendor/chat",
        "system_one_model": "vendor/jev",
    }
    effective = effective_provider_settings()
    assert effective.openrouter_api_key.get_secret_value() == "saved-secret"
    assert effective.openrouter_model == "vendor/chat"
    assert effective.system_one_model == "vendor/jev"
    assert (
        api.put(
            "/api/providers/openrouter",
            json={"openrouter_model": "bad model", "system_one_model": "jev"},
        ).status_code
        == 422
    )
    assert store["openrouter"] == "saved-secret"


def test_public_model_catalog_and_error(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    request = httpx.Request("GET", "https://openrouter.ai/api/v1/models")

    def get(url, **kwargs):
        assert "headers" not in kwargs
        return httpx.Response(
            200,
            request=request,
            json={
                "data": [
                    {
                        "id": "vendor/a",
                        "name": "A",
                        "pricing": {"prompt": "0.000001", "completion": "0.000002"},
                    },
                    {"invalid": "item"},
                ]
            },
        )

    monkeypatch.setattr(httpx, "get", get)
    api = client()
    result = api.get("/api/providers/openrouter/models")
    assert result.headers["X-Model-Cache"] == "fresh"
    assert result.json() == [
        {
            "id": "vendor/a",
            "name": "A",
            "pricing": {"prompt": "0.000001", "completion": "0.000002"},
        }
    ]

    def decisions(url, **kwargs):
        assert kwargs["params"] == {"output_modalities": "decisions"}
        return httpx.Response(
            200,
            request=request,
            json={
                "data": [
                    {"id": "typesafe/jev-1.14", "endpoints": ["/api/alpha/decisions"]},
                    {"id": "vendor/extractor", "endpoints": ["/api/alpha/extractions"]},
                ]
            },
        )

    monkeypatch.setattr(httpx, "get", decisions)
    assert api.get("/api/providers/openrouter/models?kind=decisions").json() == [
        {"id": "typesafe/jev-1.14", "name": "typesafe/jev-1.14"}
    ]
    assert api.get("/api/providers/openrouter/models?kind=invalid").status_code == 422

    def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "get", fail)
    cached = api.get("/api/providers/openrouter/models")
    assert cached.status_code == 200
    assert cached.headers["X-Model-Cache"] == "stale"
    assert cached.json() == result.json()
    assert (
        api.get("/api/providers/openrouter/models?kind=decisions").json()[0]["id"]
        == "typesafe/jev-1.14"
    )
    (tmp_path / ".archhypoflow/cache/openrouter/general.json").unlink()
    assert api.get("/api/providers/openrouter/models").status_code == 502
