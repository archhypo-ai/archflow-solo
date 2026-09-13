"""Public configuration API for ArchWise."""

from .settings import DEFAULT_OPENROUTER_MODEL, AgentSettings, settings
from .version import PACKAGE_VERSION

__all__ = [
    "DEFAULT_OPENROUTER_MODEL",
    "PACKAGE_VERSION",
    "AgentSettings",
    "settings",
]
