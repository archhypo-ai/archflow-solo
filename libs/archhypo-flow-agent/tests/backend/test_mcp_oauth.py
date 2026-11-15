import asyncio
import json
import logging
from urllib.parse import parse_qs, urlparse

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from keyring.errors import NoKeyringError
from mcp.shared.auth import OAuthToken

from archhypo_flow_agent.backend.app import _OAuthCallbackLogFilter
from archhypo_flow_agent.backend.controllers.mcps import router
from archhypo_flow_agent.services.mcp_manager import MCPManager
from archhypo_flow_agent.services.mcp_oauth import (
    KeyringTokenStorage,
    OAuthCoordinator,
    OAuthCredentialError,
)


def test_oauth_discovery_registration_pkce_and_keyring(monkeypatch):
    stored = {}
    monkeypatch.setattr(
        "keyring.get_password", lambda service, key: stored.get((service, key))
    )
    monkeypatch.setattr(
        "keyring.set_password",
        lambda service, key, value: stored.__setitem__((service, key), value),
    )
    requests = []

    async def run():
        coordinator = OAuthCoordinator()

        async def redirect(url):
            query = parse_qs(urlparse(url).query)
            assert query["code_challenge_method"] == ["S256"]
            assert coordinator.complete(query["state"][0], "test-code", "")

        provider = coordinator.create_provider(
            "server", "https://mcp.example.com/v1", redirect
        )

        def handler(request):
            requests.append(request)
            path = request.url.path
            if path == "/v1":
                if request.headers.get("authorization") == "Bearer access-secret":
                    return httpx.Response(200, json={"ok": True})
                return httpx.Response(
                    401,
                    headers={
                        "WWW-Authenticate": 'Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource/v1"'
                    },
                )
            if path == "/.well-known/oauth-protected-resource/v1":
                return httpx.Response(
                    200,
                    json={
                        "resource": "https://mcp.example.com/v1",
                        "authorization_servers": ["https://auth.example.com"],
                        "scopes_supported": ["read"],
                    },
                )
            if path == "/.well-known/oauth-authorization-server":
                return httpx.Response(
                    200,
                    json={
                        "issuer": "https://auth.example.com",
                        "authorization_endpoint": "https://auth.example.com/authorize",
                        "token_endpoint": "https://auth.example.com/token",
                        "registration_endpoint": "https://auth.example.com/register",
                        "response_types_supported": ["code"],
                        "code_challenge_methods_supported": ["S256"],
                    },
                )
            if path == "/register":
                metadata = json.loads(request.content)
                return httpx.Response(201, json={**metadata, "client_id": "client-id"})
            if path == "/token":
                data = parse_qs(request.content.decode())
                assert data["code"] == ["test-code"]
                assert data["code_verifier"]
                return httpx.Response(
                    200,
                    json={
                        "access_token": "access-secret",
                        "token_type": "Bearer",
                        "refresh_token": "refresh-secret",
                        "expires_in": 3600,
                        "scope": "read",
                    },
                )
            return httpx.Response(404)

        async with httpx.AsyncClient(
            auth=provider, transport=httpx.MockTransport(handler)
        ) as client:
            response = await client.get("https://mcp.example.com/v1")
        assert response.status_code == 200
        assert not coordinator.pending
        tokens = await KeyringTokenStorage(
            "server", "https://mcp.example.com/v1"
        ).get_tokens()
        assert tokens and tokens.refresh_token == "refresh-secret"
        assert (
            await KeyringTokenStorage(
                "other", "https://mcp.example.com/v1"
            ).get_tokens()
            is None
        )
        assert (
            await KeyringTokenStorage(
                "server", "https://other.example.com/v1"
            ).get_tokens()
            is None
        )

    asyncio.run(run())
    assert any(req.url.path == "/token" for req in requests)
    assert all("access-secret" not in key for _, key in stored)


def test_callback_rejects_unknown_state_and_is_one_time():
    application = FastAPI()
    application.state.mcp_manager = MCPManager()
    application.include_router(router)
    with TestClient(application) as client:
        assert (
            client.get("/api/mcps/oauth/callback?state=unknown&code=secret").status_code
            == 400
        )
        assert client.get("/api/mcps/oauth/callback").status_code == 400


def test_oauth_callback_is_one_time_and_cancellation_cleans_up():
    async def run():
        coordinator = OAuthCoordinator()
        urls = []

        async def redirect(url):
            urls.append(url)

        provider = coordinator.create_provider(
            "id", "https://example.com/mcp", redirect
        )
        await provider.context.redirect_handler(
            "https://auth.example.com/authorize?state=abc"
        )
        assert not coordinator.complete("wrong", "code", "")
        assert coordinator.complete("abc", "code", "")
        assert not coordinator.complete("abc", "code", "")
        assert await provider.context.callback_handler() == ("code", "abc")

        provider = coordinator.create_provider(
            "id", "https://example.com/mcp", redirect
        )
        await provider.context.redirect_handler(
            "https://auth.example.com/authorize?state=def"
        )
        task = asyncio.create_task(provider.context.callback_handler())
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        assert not coordinator.pending

    asyncio.run(run())


def test_oauth_callback_query_is_not_written_to_uvicorn_access_log():
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "",
        0,
        '%s "%s %s HTTP/%s" %d',
        ("127.0.0.1", "GET", "/api/mcps/oauth/callback?code=secret", "1.1", 200),
        None,
    )
    assert not _OAuthCallbackLogFilter().filter(record)


def test_locked_keyring_does_not_store_secrets_elsewhere(monkeypatch):
    def fail(*_args):
        raise NoKeyringError("no keyring")

    monkeypatch.setattr("keyring.get_password", fail)
    monkeypatch.setattr("keyring.set_password", fail)

    async def run():
        storage = KeyringTokenStorage("server", "https://example.com")
        assert await storage.get_tokens() is None
        try:
            await storage.set_tokens(
                OAuthToken(access_token="secret", token_type="Bearer")
            )
        except OAuthCredentialError:
            pass
        else:
            raise AssertionError("locked keyring must fail closed")

    asyncio.run(run())
