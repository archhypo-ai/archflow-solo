"""Package metadata used by runtime adapters."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    PACKAGE_VERSION = version("archwise-agent")
except PackageNotFoundError:
    # Allows direct source-tree imports outside an installed environment.
    PACKAGE_VERSION = "0.1.0"

__all__ = ["PACKAGE_VERSION"]
