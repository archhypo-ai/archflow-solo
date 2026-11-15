"""Endpoints for the MCP gallery and manually managed connections."""

from fastapi import APIRouter, HTTPException, Request

from archhypo_flow_agent.services.mcp_manager import (
    MCPManager,
    ServerConfig,
    ServerInput,
    config_path,
    read_config,
    write_config,
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


@router.post("", status_code=201)
async def add_server(payload: ServerInput, request: Request) -> dict:
    configs = _configs()
    if payload.id in configs:
        raise HTTPException(409, "Server ID already exists")
    config = ServerConfig.model_validate(payload.model_dump(exclude={"id"}))
    configs[payload.id] = config
    _write(configs)
    return _entry(payload.id, config, request.app.state.mcp_manager)


@router.post("/folder")
async def folder() -> dict[str, str]:
    path = config_path().parent
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise HTTPException(500, "Could not create configuration folder") from error
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
async def connect_server(server_id: str, request: Request) -> dict:
    configs = _configs()
    if server_id not in configs:
        raise HTTPException(404, "Server not found")
    manager: MCPManager = request.app.state.mcp_manager
    await manager.connect(server_id, configs[server_id])
    return _entry(server_id, configs[server_id], manager)


@router.post("/{server_id}/disconnect")
async def disconnect_server(server_id: str, request: Request) -> dict:
    configs = _configs()
    if server_id not in configs:
        raise HTTPException(404, "Server not found")
    manager: MCPManager = request.app.state.mcp_manager
    await manager.disconnect(server_id)
    return _entry(server_id, configs[server_id], manager)
