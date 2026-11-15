"""Tool settings and credentials stored in the operating system keyring."""

import json
import os
import tempfile
from pathlib import Path
from typing import Literal

import keyring
from keyring.errors import KeyringError

from archhypo_flow_agent.config import settings

ToolId = Literal["tavily", "exa"]
SERVICE = "archhypo-flow-tools"


def _path(tool_id: ToolId) -> Path:
    root = Path.home() / ".archhypoflow"
    folder = root / "tools"
    path = folder / f"{tool_id}.json"
    if root.is_symlink() or folder.is_symlink() or path.is_symlink():
        raise ValueError("Tool configuration cannot use symbolic links")
    return path


def read_config(tool_id: ToolId) -> dict:
    path = _path(tool_id)
    if not path.exists():
        return {"enabled": True}
    if path.stat().st_size > 64000:
        raise ValueError("Tool configuration is too large")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("enabled", True), bool):
        raise ValueError("Invalid tool configuration")
    return {"enabled": data.get("enabled", True)}


def write_config(tool_id: ToolId, enabled: bool) -> None:
    path = _path(tool_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            name = stream.name
            json.dump({"enabled": enabled}, stream, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def environment_variable(tool_id: ToolId) -> str:
    return f"{tool_id.upper()}_API_KEY"


def get_key(tool_id: ToolId) -> str:
    try:
        value = keyring.get_password(SERVICE, tool_id)
    except KeyringError:
        value = None
    if value and value.strip():
        return value.strip()
    if tool_id == "tavily" and settings.tavily_api_key:
        return settings.tavily_api_key.get_secret_value().strip()
    return os.environ.get(environment_variable(tool_id), "").strip()


def is_available(tool_id: ToolId) -> bool:
    try:
        return bool(read_config(tool_id)["enabled"] and get_key(tool_id))
    except (OSError, ValueError):
        return False
