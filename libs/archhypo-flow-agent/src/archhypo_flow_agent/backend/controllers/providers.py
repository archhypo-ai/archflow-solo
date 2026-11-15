"""Provider configuration and the public OpenRouter model catalog."""

from typing import Any, Literal

import httpx
import keyring
from fastapi import APIRouter, HTTPException, Response
from keyring.errors import KeyringError
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from archhypo_flow_agent.config.provider_config import (
    SERVICE,
    effective_provider_settings,
    read_provider_settings,
    save_provider_settings,
    update_provider_settings,
)
from archhypo_flow_agent.services.model_catalog_cache import read_cache, write_cache

router = APIRouter(prefix="/api/providers", tags=["providers"])


class ProviderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    openrouter_model: str = Field(min_length=1, max_length=300)
    system_one_model: str = Field(min_length=1, max_length=300)
    api_key: SecretStr | None = None

    @field_validator("openrouter_model", "system_one_model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        value = value.strip()
        if not value or any(char.isspace() or ord(char) < 32 for char in value):
            raise ValueError("Invalid model identifier")
        return value


class ObservabilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool
    api_key: SecretStr | None = None
    public_key: SecretStr | None = None
    secret_key: SecretStr | None = None


def _has_key(value: SecretStr | None) -> bool:
    return bool(value and value.get_secret_value().strip())


def _observability_entry(provider: Literal["langfuse", "langsmith"]) -> dict:
    config = effective_provider_settings()
    if provider == "langfuse":
        keys = {
            "public_key": _has_key(config.langfuse_public_key),
            "secret_key": _has_key(config.langfuse_secret_key),
        }
        enabled = config.langfuse_enabled
    else:
        keys = {"api_key": _has_key(config.langsmith_api_key)}
        enabled = config.langsmith_tracing
    return {
        "id": provider,
        "name": "Langfuse" if provider == "langfuse" else "LangSmith",
        "enabled": enabled,
        "configured": all(keys.values()),
        "keys": keys,
    }


@router.get("/observability")
def list_observability() -> list[dict]:
    try:
        return [_observability_entry("langfuse"), _observability_entry("langsmith")]
    except (OSError, ValueError) as error:
        raise HTTPException(500, "Could not read provider settings") from error


@router.put("/observability/{provider}")
def update_observability(
    provider: Literal["langfuse", "langsmith"], update: ObservabilityUpdate
) -> dict:
    fields = {"langfuse": ("public_key", "secret_key"), "langsmith": ("api_key",)}[
        provider
    ]
    if any(
        getattr(update, field) is not None
        for field in {"api_key", "public_key", "secret_key"} - set(fields)
    ):
        raise HTTPException(400, "Invalid credential field")
    try:
        read_provider_settings()
        for field in fields:
            secret = getattr(update, field)
            if secret is not None:
                key = secret.get_secret_value().strip()
                if not key:
                    raise HTTPException(400, "Credential cannot be empty")
                keyring.set_password(SERVICE, f"{provider}_{field}", key)
        flag = "langfuse_enabled" if provider == "langfuse" else "langsmith_tracing"
        update_provider_settings({flag: update.enabled})
        return _observability_entry(provider)
    except KeyringError as error:
        raise HTTPException(503, "System credential store is unavailable") from error
    except (OSError, ValueError) as error:
        raise HTTPException(500, "Could not save provider settings") from error


@router.get("/openrouter")
def get_openrouter_settings() -> dict:
    try:
        config = effective_provider_settings()
    except (OSError, ValueError) as error:
        raise HTTPException(500, "Could not read provider settings") from error
    return {
        "configured": bool(
            config.openrouter_api_key
            and config.openrouter_api_key.get_secret_value().strip()
        ),
        "openrouter_model": config.openrouter_model,
        "system_one_model": config.system_one_model or "",
    }


@router.put("/openrouter")
def update_openrouter_settings(update: ProviderUpdate) -> dict:
    try:
        read_provider_settings()
        if update.api_key is not None:
            key = update.api_key.get_secret_value().strip()
            if not key:
                raise HTTPException(400, "API key cannot be empty")
            keyring.set_password(SERVICE, "openrouter", key)
        save_provider_settings(update.openrouter_model, update.system_one_model)
    except KeyringError as error:
        raise HTTPException(503, "System credential store is unavailable") from error
    except (OSError, ValueError) as error:
        raise HTTPException(500, "Could not save provider settings") from error
    return get_openrouter_settings()


def _model_item(item: dict) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": item["id"],
        "name": str(item.get("name") or item["id"])[:300],
    }
    pricing = item.get("pricing")
    if isinstance(pricing, dict):
        result["pricing"] = {
            field: value
            for field in ("prompt", "completion")
            if isinstance(value := pricing.get(field), str) and len(value) <= 64
        }
    return result


@router.get("/openrouter/models")
def list_openrouter_models(
    response: Response,
    kind: Literal["general", "decisions"] = "general",
) -> list[dict[str, Any]]:
    try:
        upstream = httpx.get(
            "https://openrouter.ai/api/v1/models",
            params={"output_modalities": "decisions"} if kind == "decisions" else None,
            timeout=15.0,
            follow_redirects=False,
        )
        upstream.raise_for_status()
        payload = upstream.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ValueError("Invalid catalog")
        models = sorted(
            [
                _model_item(item)
                for item in payload["data"][:10000]
                if isinstance(item, dict)
                and isinstance(item.get("id"), str)
                and 0 < len(item["id"]) <= 300
                and (
                    kind == "general"
                    or (
                        isinstance(item.get("endpoints"), list)
                        and "/api/alpha/decisions" in item["endpoints"]
                    )
                )
            ],
            key=lambda item: item["name"].casefold(),
        )
        if not models:
            raise ValueError("Empty model catalog")
        write_cache(kind, models)
        response.headers["X-Model-Cache"] = "fresh"
        return models
    except (httpx.HTTPError, ValueError) as error:
        cached = read_cache(kind)
        if cached is not None:
            response.headers["X-Model-Cache"] = "stale"
            return cached
        raise HTTPException(502, "Could not load OpenRouter model catalog") from error
