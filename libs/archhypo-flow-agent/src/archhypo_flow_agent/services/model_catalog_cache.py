"""Local, independent last-successful OpenRouter catalog snapshots."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Literal

CatalogKind = Literal["general", "decisions"]


def _path(kind: CatalogKind) -> Path:
    root = Path.home() / ".archhypoflow"
    cache = root / "cache"
    folder = cache / "openrouter"
    path = folder / f"{kind}.json"
    if any(p.is_symlink() for p in (root, cache, folder, path)):
        raise ValueError("Catalog cache cannot use symbolic links")
    return path


def read_cache(kind: CatalogKind) -> list[dict[str, Any]] | None:
    try:
        path = _path(kind)
        if not path.exists() or path.stat().st_size > 5_000_000:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data or len(data) > 10_000:
            return None
        if any(
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not isinstance(item.get("name"), str)
            or not item["id"]
            or len(item["id"]) > 300
            or len(item["name"]) > 300
            for item in data
        ):
            return None
        result = []
        for item in data:
            model: dict[str, Any] = {"id": item["id"], "name": item["name"]}
            if isinstance(item.get("pricing"), dict):
                model["pricing"] = {
                    field: value
                    for field in ("prompt", "completion")
                    if isinstance(value := item["pricing"].get(field), str)
                    and len(value) <= 64
                }
            result.append(model)
        return result
    except (OSError, ValueError):
        return None


def write_cache(kind: CatalogKind, models: list[dict[str, Any]]) -> None:
    if not models:
        return
    filename = ""
    try:
        path = _path(kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            filename = stream.name
            json.dump(models, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(filename, path)
    except (OSError, ValueError):
        pass  # A read-only cache must not prevent using the live catalog.
    finally:
        if filename and os.path.exists(filename):
            os.unlink(filename)
