"""OAuth support for remote MCP servers using the system credential store."""

from __future__ import annotations

import asyncio
import hashlib
from urllib.parse import parse_qs, urlparse

import keyring
from keyring.errors import KeyringError, PasswordDeleteError
from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from pydantic import ValidationError

SERVICE = "archhypo-flow-mcp-oauth"
CALLBACK_URL = "http://127.0.0.1:8765/api/mcps/oauth/callback"


class OAuthCredentialError(RuntimeError):
    """The operating system credential store is unavailable."""


class KeyringTokenStorage:
    """Bind credentials to both server identity and URL, never to mcp.json."""

    def __init__(self, server_id: str, url: str) -> None:
        digest = hashlib.sha256(url.encode()).hexdigest()
        self.account = f"{server_id}:{digest}"

    async def _get(self, kind: str) -> str | None:
        try:
            return await asyncio.to_thread(
                keyring.get_password, SERVICE, f"{self.account}:{kind}"
            )
        except KeyringError:
            # Public servers must remain usable on systems without a keyring.
            return None

    async def _set(self, kind: str, value: str) -> None:
        try:
            await asyncio.to_thread(
                keyring.set_password, SERVICE, f"{self.account}:{kind}", value
            )
        except KeyringError as error:
            raise OAuthCredentialError(
                "System credential store is unavailable or locked"
            ) from error

    async def get_tokens(self) -> OAuthToken | None:
        value = await self._get("tokens")
        try:
            return OAuthToken.model_validate_json(value) if value else None
        except ValidationError as error:
            raise OAuthCredentialError("Stored MCP OAuth tokens are invalid") from error

    async def set_tokens(self, tokens: OAuthToken) -> None:
        await self._set("tokens", tokens.model_dump_json())

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        value = await self._get("client")
        try:
            return (
                OAuthClientInformationFull.model_validate_json(value) if value else None
            )
        except ValidationError as error:
            raise OAuthCredentialError(
                "Stored MCP OAuth client data is invalid"
            ) from error

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        await self._set("client", client_info.model_dump_json())

    async def clear(self) -> None:
        for kind in ("tokens", "client"):
            try:
                await asyncio.to_thread(
                    keyring.delete_password, SERVICE, f"{self.account}:{kind}"
                )
            except PasswordDeleteError:
                pass
            except KeyringError as error:
                raise OAuthCredentialError(
                    "System credential store is unavailable or locked"
                ) from error


class OAuthCoordinator:
    """Keep one-time callback states in memory and let the SDK verify them."""

    def __init__(self) -> None:
        self.pending: dict[str, asyncio.Future[tuple[str, str | None]]] = {}
        self.presentation: dict[str, tuple[str | None, str | None]] = {}

    def create_provider(
        self,
        server_id: str,
        url: str,
        on_redirect,
        *,
        theme: str | None = None,
        language: str | None = None,
    ) -> OAuthClientProvider:
        future: asyncio.Future[tuple[str, str | None]] = (
            asyncio.get_running_loop().create_future()
        )
        state_holder: list[str] = []

        async def redirect(authorization_url: str) -> None:
            resource = urlparse(url)
            if resource.scheme != "https" and resource.hostname not in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                raise ValueError("OAuth requires HTTPS for remote MCP servers")
            parsed = urlparse(authorization_url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("OAuth authorization endpoint must use HTTPS")
            state = parse_qs(parsed.query).get("state", [""])[0]
            if not state:
                raise ValueError("OAuth authorization request has no state")
            state_holder.append(state)
            self.pending[state] = future
            self.presentation[state] = (theme, language)
            await on_redirect(authorization_url)

        async def callback() -> tuple[str, str | None]:
            try:
                return await asyncio.wait_for(future, timeout=300)
            finally:
                for state in state_holder:
                    self.pending.pop(state, None)
                    self.presentation.pop(state, None)

        metadata = OAuthClientMetadata.model_validate(
            {
                "client_name": "ArchHypo Flow",
                "redirect_uris": [CALLBACK_URL],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            }
        )
        return OAuthClientProvider(
            server_url=url,
            client_metadata=metadata,
            storage=KeyringTokenStorage(server_id, url),
            redirect_handler=redirect,
            callback_handler=callback,
        )

    def complete(self, state: str, code: str, error: str) -> bool:
        future = self.pending.pop(state, None)
        self.presentation.pop(state, None)
        if future is None or future.done():
            return False
        if error:
            future.set_exception(ValueError("OAuth authorization was denied or failed"))
        elif code:
            future.set_result((code, state))
        else:
            future.set_exception(ValueError("OAuth authorization returned no code"))
        return True
