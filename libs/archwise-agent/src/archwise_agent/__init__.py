"""Public API for the ArchWise agent package."""

from .agents import (
    build_archwise_agent,
    build_classifier_agent,
    build_hypothesis_agent,
    build_request_router_agent,
    build_response_agent,
    build_technical_plan_agent,
)
from .config import PACKAGE_VERSION, AgentSettings, settings
from .core import (
    AgentState,
    ArchHypo,
    ArchHypoState,
    Hypothesis,
    HypothesisClassification,
    RequestRoute,
    RequestRouting,
    TechnicalPlan,
    UserResponse,
)
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
    "ArchHypo",
    "ArchHypoState",
    "Hypothesis",
    "HypothesisClassification",
    "RequestRoute",
    "RequestRouting",
    "TechnicalPlan",
    "UserResponse",
    "build_agent",
    "build_archwise_agent",
    "build_classifier_agent",
    "build_hypothesis_agent",
    "build_request_router_agent",
    "build_response_agent",
    "build_technical_plan_agent",
    "settings",
]
