import json
import socket
import subprocess
import sys
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
