"""Catalog and operating-system credential settings for tools."""

from typing import Literal

import keyring
from fastapi import APIRouter, HTTPException
from keyring.errors import KeyringError
from pydantic import BaseModel, ConfigDict, SecretStr

from archhypo_flow_agent.config.tool_config import (
    SERVICE,
    environment_variable,
    get_key,
    read_config,
    write_config,
)

router = APIRouter(prefix="/api/tool-catalog", tags=["tool-catalog"])
ToolId = Literal["tavily", "exa"]


class ToolConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool
    api_key: SecretStr | None = None


def _entry(tool_id: ToolId) -> dict:
    try:
        config = read_config(tool_id)
        configured = bool(get_key(tool_id))
    except (OSError, ValueError) as error:
        raise HTTPException(500, "Could not read tool configuration") from error
    return {
        "id": tool_id,
        "name": tool_id.title(),
        "api_key_env": environment_variable(tool_id),
        "enabled": config["enabled"],
        "configured": configured,
    }


@router.get("")
def list_tools() -> list[dict]:
    return [_entry("tavily"), _entry("exa")]


@router.get("/{tool_id}")
def get_tool(tool_id: ToolId) -> dict:
    return _entry(tool_id)


@router.put("/{tool_id}")
def save_tool(tool_id: ToolId, config: ToolConfiguration) -> dict:
    # A missing key leaves the existing credential untouched; never return it.
    try:
        read_config(tool_id)
        if config.api_key is not None:
            value = config.api_key.get_secret_value().strip()
            if not value:
                raise HTTPException(400, "API key cannot be empty")
            keyring.set_password(SERVICE, tool_id, value)
        write_config(tool_id, config.enabled)
    except KeyringError as error:
        raise HTTPException(503, "System credential store is unavailable") from error
    except (OSError, ValueError) as error:
        raise HTTPException(500, "Could not save tool configuration") from error
    return _entry(tool_id)
