"""Public API for the ArchWise agent package."""

from .agents import build_archwise_agent, build_chat_agent
from .config import AgentSettings, PACKAGE_VERSION, settings
from .core import AgentState
from .services import AgentService, AgentStreamEvent, AgentTurn

# Short public entrypoint for the current orchestrator.
build_agent = build_archwise_agent

__all__ = [
    "AgentService",
    "AgentSettings",
    "AgentStreamEvent",
    "PACKAGE_VERSION",
    "AgentState",
    "AgentTurn",
    "build_agent",
    "build_archwise_agent",
    "build_chat_agent",
    "settings",
]
