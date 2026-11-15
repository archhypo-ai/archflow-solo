"""Local storage paths for the ArchHypo Flow runtime."""

from __future__ import annotations

import os
from pathlib import Path


def _storage_root() -> Path:
    configured = os.getenv("ARCHHYPO_FLOW_STORAGE_ROOT")
    if configured:
        return Path(configured).expanduser()

    return Path.home() / ".archhypoflow"


STORAGE_ROOT = _storage_root()
RUNTIME_ROOT = STORAGE_ROOT / "runtime"
DATABASE_PATH = RUNTIME_ROOT / "checkpoints.sqlite"

__all__ = ["DATABASE_PATH", "RUNTIME_ROOT", "STORAGE_ROOT"]
