"""Public ArchWise agent builders."""

from .orchestrator import build_archwise_agent

# Compatibility-friendly name for the current generic chat workflow.
build_chat_agent = build_archwise_agent

__all__ = ["build_archwise_agent", "build_chat_agent"]
