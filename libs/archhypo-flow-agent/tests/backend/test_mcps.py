import json
import socket
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.backend.controllers.mcps import router
from archhypo_flow_agent.services.mcp_manager import MCPManager


def app() -> FastAPI:
    application = FastAPI()
    application.state.mcp_manager = MCPManager()
    application.include_router(router)
    return application


def test_edit_file_creates_missing_file_and_preserves_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = tmp_path / ".archhypoflow/mcp.json"
    with TestClient(app()) as client:
        response = client.post("/api/mcps/file")
        assert response.status_code == 200
        assert response.json() == {"path": str(path)}
        assert json.loads(path.read_text()) == {"mcpServers": {}}
        path.write_text("invalid but user-owned content", encoding="utf-8")
        assert client.post("/api/mcps/file").status_code == 200
        assert path.read_text(encoding="utf-8") == "invalid but user-owned content"


def test_startup_connects_only_after_manual_connection(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    script = tmp_path / "server.py"
    script.write_text("""from mcp.server.fastmcp import FastMCP
mcp = FastMCP("startup")
@mcp.tool()
def echo(message: str) -> str:
    return message
mcp.run(transport="stdio")
""")
    path = tmp_path / ".archhypoflow/mcp.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "default": {"command": sys.executable, "args": [str(script)]},
                    "disabled": {"command": sys.executable, "args": [str(script)]},
                    "failing": {
                        "command": "nonexistent-mcp-command",
                        "auto_connect": True,
                    },
                }
            }
        )
    )
    application = create_app(agent_service=SimpleNamespace(chat_ready=False))
    with TestClient(application) as client:
        assert {item["id"]: item["status"] for item in client.get("/api/mcps").json()}[
            "default"
        ] == "disconnected"
        assert client.post("/api/mcps/default/connect").status_code == 200
        assert (
            json.loads(path.read_text())["mcpServers"]["default"]["auto_connect"]
            is True
        )
        for _ in range(100):
            servers = {item["id"]: item for item in client.get("/api/mcps").json()}
            if (
                servers["default"]["status"] == "connected"
                and servers["failing"]["status"] == "error"
            ):
                break
            time.sleep(0.05)
        assert servers["default"]["status"] == "connected"
        assert servers["default"]["tools"][0]["name"] == "echo"
        assert servers["disabled"]["status"] == "disconnected"
        assert servers["failing"]["status"] == "error"
    assert not application.state.mcp_manager.tasks
    restarted = create_app(agent_service=SimpleNamespace(chat_ready=False))
    with TestClient(restarted) as client:
        for _ in range(100):
            servers = {item["id"]: item for item in client.get("/api/mcps").json()}
            if servers["default"]["status"] == "connected":
                break
            time.sleep(0.05)
        assert servers["default"]["status"] == "connected"
        assert servers["disabled"]["status"] == "disconnected"
        assert (
            client.post("/api/mcps/default/disconnect").json()["status"]
            == "disconnected"
        )
        assert not json.loads(path.read_text())["mcpServers"]["default"].get(
            "auto_connect", False
        )
    assert not restarted.state.mcp_manager.tasks
    final_app = create_app(agent_service=SimpleNamespace(chat_ready=False))
    with TestClient(final_app) as client:
        servers = {item["id"]: item for item in client.get("/api/mcps").json()}
        assert servers["default"]["status"] == "disconnected"
        assert servers["disabled"]["status"] == "disconnected"


def test_invalid_config_does_not_prevent_application_startup(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = tmp_path / ".archhypoflow/mcp.json"
    path.parent.mkdir()
    path.write_text("invalid json")
    with TestClient(
        create_app(agent_service=SimpleNamespace(chat_ready=False))
    ) as client:
        assert client.get("/api/mcps").status_code == 400


def test_config_crud_and_transport_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with TestClient(app()) as client:
        assert client.get("/api/mcps").json() == []
        assert (
            client.post(
                "/api/mcps", json={"id": "bad", "transport": "sse", "url": "not-url"}
            ).status_code
            == 422
        )
        data = {
            "id": "local",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "test"],
            "env": {"TOKEN": "${MY_TOKEN}"},
        }
        assert client.post("/api/mcps", json=data).status_code == 201
        assert client.post("/api/mcps", json=data).status_code == 409
        config = json.loads((tmp_path / ".archhypoflow/mcp.json").read_text())
        assert config["mcpServers"]["local"]["env"]["TOKEN"] == "${MY_TOKEN}"
        assert client.get("/api/mcps").json()[0]["status"] == "disconnected"
        assert (
            client.put("/api/mcps/local", json={**data, "command": "node"}).status_code
            == 200
        )
        assert client.delete("/api/mcps/local").status_code == 204
        assert client.get("/api/mcps").json() == []


def test_missing_environment_variable_reports_connection_error(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("MCP_TEST_MISSING", raising=False)
    with TestClient(app()) as client:
        payload = {
            "id": "missing",
            "command": "npx",
            "env": {"TOKEN": "${MCP_TEST_MISSING}"},
        }
        assert client.post("/api/mcps", json=payload).status_code == 201
        assert client.post("/api/mcps/missing/connect").status_code == 200
        for _ in range(50):
            server = client.get("/api/mcps").json()[0]
            if server["status"] == "error":
                break
            time.sleep(0.02)
        assert server["status"] == "error"
        assert "MCP_TEST_MISSING" in server["error"]


def test_stdio_connect_discovers_tools_and_disconnects(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    script = tmp_path / "server.py"
    script.write_text('''from mcp.server.fastmcp import FastMCP
mcp = FastMCP("fixture")
@mcp.tool()
def echo(message: str) -> str:
    """Echo a message."""
    return message
mcp.run(transport="stdio")
''')
    with TestClient(app()) as client:
        data = {
            "id": "fixture",
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(script)],
        }
        assert client.post("/api/mcps", json=data).status_code == 201
        assert client.post("/api/mcps/fixture/connect").status_code == 200
        for _ in range(100):
            server = client.get("/api/mcps").json()[0]
            if server["status"] in ("connected", "error"):
                break
            time.sleep(0.05)
        assert server["status"] == "connected", server
        assert server["tools"][0]["name"] == "echo"
        assert "message" in server["tools"][0]["inputSchema"]["properties"]
        assert (
            client.post("/api/mcps/fixture/disconnect").json()["status"]
            == "disconnected"
        )


@pytest.mark.parametrize("transport,path", [("sse", "sse"), ("streamable-http", "mcp")])
def test_remote_transports_discover_tools(tmp_path, monkeypatch, transport, path):
    monkeypatch.setenv("HOME", str(tmp_path))
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    script = tmp_path / "remote_server.py"
    script.write_text(f"""from mcp.server.fastmcp import FastMCP
mcp = FastMCP("fixture", host="127.0.0.1", port={port})
@mcp.tool()
def echo(message: str) -> str:
    return message
mcp.run(transport={transport!r})
""")
    process = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.05)
        with TestClient(app()) as client:
            data = {
                "id": "remote",
                "transport": transport,
                "url": f"http://127.0.0.1:{port}/{path}",
            }
            assert client.post("/api/mcps", json=data).status_code == 201
            assert client.post("/api/mcps/remote/connect").status_code == 200
            for _ in range(100):
                server = client.get("/api/mcps").json()[0]
                if server["status"] in ("connected", "error"):
                    break
                time.sleep(0.05)
            assert server["status"] == "connected", server
            assert server["tools"][0]["name"] == "echo"
            assert (
                client.post("/api/mcps/remote/disconnect").json()["status"]
                == "disconnected"
            )
    finally:
        process.terminate()
        process.wait(timeout=10)
