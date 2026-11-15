"""Endpoints for the MCP gallery and manually managed connections."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from archhypo_flow_agent.backend.oauth_page import render_oauth_page
from archhypo_flow_agent.services.mcp_manager import (
    MCPManager,
    ServerConfig,
    ServerInput,
    config_path,
    read_config,
    write_config,
)
from archhypo_flow_agent.services.mcp_oauth import (
    KeyringTokenStorage,
    OAuthCredentialError,
)

router = APIRouter(prefix="/api/mcps", tags=["mcps"])


def _configs() -> dict[str, ServerConfig]:
    try:
        return read_config()
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


def _write(configs: dict[str, ServerConfig]) -> None:
    try:
        write_config(configs)
    except (OSError, ValueError) as error:
        raise HTTPException(500, "Could not save mcp.json") from error


def _entry(server_id: str, config: ServerConfig, manager: MCPManager) -> dict:
    return {"id": server_id, **config.model_dump(), **manager.status(server_id)}


@router.get("")
async def list_servers(request: Request) -> list[dict]:
    manager: MCPManager = request.app.state.mcp_manager
    configs = _configs()
    for server_id, connected_config in list(manager.configurations.items()):
        if configs.get(server_id) != connected_config:
            await manager.disconnect(server_id)
    return [_entry(key, config, manager) for key, config in configs.items()]


@router.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(
    request: Request, state: str = "", code: str = "", error: str = ""
) -> HTMLResponse:
    manager: MCPManager = request.app.state.mcp_manager
    theme, language = manager.oauth.presentation.get(state, (None, None))
    accepted = bool(state) and manager.oauth.complete(state, code, error)
    page = render_oauth_page(
        success=bool(accepted and not error and code),
        language=language or request.headers.get("accept-language", "en"),
        theme=theme,
    )
    return HTMLResponse(
        page,
        status_code=200 if accepted else 400,
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": (
                "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
                "base-uri 'none'; frame-ancestors 'none'"
            ),
        },
    )


class OAuthPresentation(BaseModel):
    state: str
    theme: str
    language: str


@router.post("/oauth/presentation", status_code=204)
async def oauth_presentation(payload: OAuthPresentation, request: Request) -> None:
    manager: MCPManager = request.app.state.mcp_manager
    if payload.state not in manager.oauth.pending:
        raise HTTPException(404, "Authorization request not found")
    manager.oauth.presentation[payload.state] = (
        payload.theme if payload.theme in {"day", "night"} else None,
        payload.language if payload.language in {"pt-BR", "en"} else None,
    )


@router.post("", status_code=201)
async def add_server(payload: ServerInput, request: Request) -> dict:
    configs = _configs()
    if payload.id in configs:
        raise HTTPException(409, "Server ID already exists")
    config = ServerConfig.model_validate(payload.model_dump(exclude={"id"}))
    config.auto_connect = False
    configs[payload.id] = config
    _write(configs)
    return _entry(payload.id, config, request.app.state.mcp_manager)


@router.post("/file")
def configuration_file() -> dict[str, str]:
    path = config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write('{\n  "mcpServers": {}\n}\n')
        except FileExistsError:
            if not path.is_file():
                raise HTTPException(400, "mcp.json is not a file") from None
    except OSError as error:
        raise HTTPException(500, "Could not create mcp.json") from error
    return {"path": str(path)}


@router.put("/{server_id}")
async def update_server(server_id: str, payload: ServerInput, request: Request) -> dict:
    configs = _configs()
    if server_id not in configs:
        raise HTTPException(404, "Server not found")
    if server_id != payload.id:
        raise HTTPException(400, "Server ID cannot be changed")
    manager: MCPManager = request.app.state.mcp_manager
    await manager.disconnect(server_id)
    config = ServerConfig.model_validate(payload.model_dump(exclude={"id"}))
    config.auto_connect = configs[server_id].auto_connect
    configs[server_id] = config
    _write(configs)
    return _entry(server_id, config, manager)


@router.delete("/{server_id}", status_code=204)
async def delete_server(server_id: str, request: Request) -> None:
    configs = _configs()
    if server_id not in configs:
        raise HTTPException(404, "Server not found")
    await request.app.state.mcp_manager.disconnect(server_id)
    del configs[server_id]
    _write(configs)


@router.post("/{server_id}/connect")
async def connect_server(
    server_id: str,
    request: Request,
    theme: str | None = None,
    language: str | None = None,
) -> dict:
    configs = _configs()
    if server_id not in configs:
        raise HTTPException(404, "Server not found")
    manager: MCPManager = request.app.state.mcp_manager
    if not configs[server_id].auto_connect:
        configs[server_id].auto_connect = True
        _write(configs)
    await manager.connect(
        server_id,
        configs[server_id],
        theme=theme if theme in {"day", "night"} else None,
        language=language if language in {"pt-BR", "en"} else None,
    )
    return _entry(server_id, configs[server_id], manager)


@router.delete("/{server_id}/authorization", status_code=204)
async def forget_authorization(server_id: str, request: Request) -> None:
    configs = _configs()
    if server_id not in configs:
        raise HTTPException(404, "Server not found")
    manager: MCPManager = request.app.state.mcp_manager
    await manager.disconnect(server_id)
    configs[server_id].auto_connect = False
    _write(configs)
    try:
        await KeyringTokenStorage(server_id, configs[server_id].url).clear()
    except OAuthCredentialError as error:
        raise HTTPException(503, str(error)) from error


@router.post("/{server_id}/disconnect")
async def disconnect_server(server_id: str, request: Request) -> dict:
    configs = _configs()
    if server_id not in configs:
        raise HTTPException(404, "Server not found")
    manager: MCPManager = request.app.state.mcp_manager
    if configs[server_id].auto_connect:
        configs[server_id].auto_connect = False
        _write(configs)
    await manager.disconnect(server_id)
    return _entry(server_id, configs[server_id], manager)
