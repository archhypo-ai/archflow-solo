"""Persist non-secret provider settings and retrieve OpenRouter credentials."""

import json
import os
import tempfile
from pathlib import Path

import keyring
from keyring.errors import KeyringError
from pydantic import SecretStr

from archhypo_flow_agent.config import AgentSettings, settings

SERVICE = "archhypo-flow-providers"


def _path() -> Path:
    root = Path.home() / ".archhypoflow"
    path = root / "providers.json"
    if root.is_symlink() or path.is_symlink():
        raise ValueError("Provider configuration cannot use symbolic links")
    return path


def read_provider_settings() -> dict:
    path = _path()
    if not path.exists():
        return {}
    if path.stat().st_size > 64_000:
        raise ValueError("Provider configuration is too large")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid provider configuration")
    for field in ("openrouter_model", "system_one_model"):
        if field in data and (
            not isinstance(data[field], str)
            or not data[field].strip()
            or len(data[field]) > 300
        ):
            raise ValueError("Invalid provider model")
    for field in ("langsmith_tracing", "langfuse_enabled"):
        if field in data and not isinstance(data[field], bool):
            raise ValueError("Invalid observability setting")
    return data


def save_provider_settings(chat_model: str, system_model: str) -> None:
    update_provider_settings(
        {"openrouter_model": chat_model, "system_one_model": system_model}
    )


def update_provider_settings(updates: dict) -> None:
    data = read_provider_settings()
    data.update(updates)
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            name = stream.name
            json.dump(data, stream, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def effective_provider_settings() -> AgentSettings:
    data = read_provider_settings()
    changes = {
        field: data[field]
        for field in (
            "openrouter_model",
            "system_one_model",
            "langsmith_tracing",
            "langfuse_enabled",
        )
        if field in data
    }
    for key_name, field in (
        ("openrouter", "openrouter_api_key"),
        ("langsmith_api_key", "langsmith_api_key"),
        ("langfuse_public_key", "langfuse_public_key"),
        ("langfuse_secret_key", "langfuse_secret_key"),
    ):
        try:
            key = keyring.get_password(SERVICE, key_name)
        except KeyringError:
            key = None
        if key and key.strip():
            changes[field] = SecretStr(key.strip())
    return settings.model_copy(update=changes)
