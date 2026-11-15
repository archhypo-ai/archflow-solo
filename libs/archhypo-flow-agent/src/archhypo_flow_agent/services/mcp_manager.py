"""Local MCP configuration and manually managed client sessions."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import get_default_environment, stdio_client
from mcp.client.streamable_http import streamable_http_client
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    command: str = ""
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str = ""
    url: str = ""

    @model_validator(mode="after")
    def validate_transport(self) -> ServerConfig:
        if self.transport == "stdio" and not self.command.strip():
            raise ValueError("Command is required")
        if self.transport != "stdio":
            parsed = urlparse(self.url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("A valid HTTP(S) URL is required")
            if parsed.username or parsed.password:
                raise ValueError("Credentials must not be included in the URL")
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) for k in self.env):
            raise ValueError("Invalid environment variable name")
        return self


class ServerInput(ServerConfig):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


def config_path() -> Path:
    return Path.home() / ".archhypoflow" / "mcp.json"


def read_config() -> dict[str, ServerConfig]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not isinstance(
            document.get("mcpServers"), dict
        ):
            raise ValueError("Expected an object with mcpServers")
        result = {}
        for server_id, value in document["mcpServers"].items():
            if not isinstance(server_id, str) or not _ID.fullmatch(server_id):
                raise ValueError(f"Invalid server ID: {server_id}")
            try:
                result[server_id] = ServerConfig.model_validate(value)
            except ValidationError as error:
                raise ValueError(
                    f"Invalid configuration for server {server_id}"
                ) from error
        return result
    except (OSError, ValueError, TypeError) as error:
        raise ValueError(f"Invalid mcp.json: {error}") from error


def write_config(servers: dict[str, ServerConfig]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    content["mcpServers"] = {
        key: value.model_dump(exclude_defaults=True) for key, value in servers.items()
    }
    name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".mcp-", delete=False
        ) as stream:
            name = stream.name
            json.dump(content, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def _resolve(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in os.environ:
            raise ValueError(f"Environment variable {key} is not defined")
        return os.environ[key]

    return _VAR.sub(replace, value)


class MCPManager:
    """Manage live sessions on the application's event loop."""

    def __init__(self) -> None:
        self.states: dict[str, dict] = {}
        self.tasks: dict[str, asyncio.Task] = {}
        self.stops: dict[str, asyncio.Event] = {}
        self.configurations: dict[str, ServerConfig] = {}

    def status(self, server_id: str) -> dict:
        return self.states.get(
            server_id, {"status": "disconnected", "tools": [], "error": None}
        )

    async def connect(self, server_id: str, config: ServerConfig) -> None:
        if server_id in self.tasks and not self.tasks[server_id].done():
            return
        self.configurations[server_id] = config.model_copy(deep=True)
        self.states[server_id] = {"status": "connecting", "tools": [], "error": None}
        stop = asyncio.Event()
        self.stops[server_id] = stop
        self.tasks[server_id] = asyncio.create_task(self._run(server_id, config, stop))

    async def _run(
        self, server_id: str, config: ServerConfig, stop: asyncio.Event
    ) -> None:
        try:
            async with AsyncExitStack() as stack:
                if config.transport == "stdio":
                    env = {
                        **get_default_environment(),
                        **{key: _resolve(value) for key, value in config.env.items()},
                    }
                    parameters = StdioServerParameters(
                        command=config.command,
                        args=config.args,
                        env=env,
                        cwd=config.cwd or None,
                    )
                    streams = await stack.enter_async_context(stdio_client(parameters))
                elif config.transport == "sse":
                    streams = await stack.enter_async_context(sse_client(config.url))
                else:
                    streams = await stack.enter_async_context(
                        streamable_http_client(config.url)
                    )
                session = await stack.enter_async_context(
                    ClientSession(streams[0], streams[1])
                )
                async with asyncio.timeout(30):
                    await session.initialize()
                    tools = []
                    cursor = None
                    while True:
                        result = await session.list_tools(cursor=cursor)
                        tools.extend(
                            {
                                "name": tool.name,
                                "description": tool.description or "",
                                "inputSchema": tool.inputSchema,
                            }
                            for tool in result.tools
                        )
                        cursor = result.nextCursor
                        if not cursor:
                            break
                self.states[server_id] = {
                    "status": "connected",
                    "tools": tools,
                    "error": None,
                }
                while not stop.is_set():
                    try:
                        await asyncio.wait_for(stop.wait(), timeout=5)
                    except TimeoutError:
                        async with asyncio.timeout(5):
                            await session.send_ping()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            cause = error
            while isinstance(cause, BaseExceptionGroup) and cause.exceptions:
                cause = cause.exceptions[0]
            self.states[server_id] = {
                "status": "error",
                "tools": [],
                "error": str(cause) or type(cause).__name__,
            }
            return
        finally:
            self.stops.pop(server_id, None)
        self.states[server_id] = {"status": "disconnected", "tools": [], "error": None}

    async def disconnect(self, server_id: str) -> None:
        task = self.tasks.get(server_id)
        if task and not task.done():
            stop = self.stops.get(server_id)
            if stop:
                stop.set()
            try:
                await asyncio.wait_for(asyncio.shield(task), 5)
            except TimeoutError:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        self.tasks.pop(server_id, None)
        self.configurations.pop(server_id, None)
        self.states[server_id] = {"status": "disconnected", "tools": [], "error": None}

    async def close(self) -> None:
        await asyncio.gather(*(self.disconnect(key) for key in list(self.tasks)))
