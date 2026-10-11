"""Canonical paths for ArchWise runtime data."""

from __future__ import annotations

from pathlib import Path

from archwise_agent.config import settings


def _find_application_root(start: Path) -> Path:
    """Find the repository root when running from the source tree."""

    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return Path.cwd()


APPLICATION_ROOT = _find_application_root(Path(__file__).resolve())

_configured_storage_root = settings.archwise_storage_root
if _configured_storage_root is None:
    STORAGE_ROOT = APPLICATION_ROOT / ".archhypo"
elif _configured_storage_root.is_absolute():
    STORAGE_ROOT = _configured_storage_root.expanduser()
else:
    STORAGE_ROOT = (APPLICATION_ROOT / _configured_storage_root).resolve()

RUNTIME_ROOT = STORAGE_ROOT / "runtime"
CHECKPOINT_DB_PATH = RUNTIME_ROOT / "checkpoints.sqlite"

__all__ = [
    "APPLICATION_ROOT",
    "CHECKPOINT_DB_PATH",
    "RUNTIME_ROOT",
    "STORAGE_ROOT",
]
