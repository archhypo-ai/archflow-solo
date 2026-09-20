"""Workflow node for discovering architectural uncertainty in an attachment."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archwise_agent.agents.uncertainty_discovery import (
    build_uncertainty_discovery_agent,
)
from archwise_agent.core import (
    ArchHypoState,
    RunContext,
    UncertaintyDiscoveryReport,
)
from archwise_agent.graph import GraphNode, raise_if_cancelled

from .direct_response_generation_node import response_history

logger = logging.getLogger(__name__)

DiscoveryRoute = Literal[
    "hypothesis_formulation",
    "direct_response_generation",
]


def create_uncertainty_discovery_node(
    model: BaseChatModel,
    *,
    agent_builder: Callable[..., Runnable[Any, Any]] = (
        build_uncertainty_discovery_agent
    ),
) -> GraphNode[ArchHypoState, RunContext]:
    """Create a node that investigates the attached workspace read-only."""

    def discover(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        root_dir = _folder_context_path(runtime)
        if root_dir is None or not root_dir.is_dir():
            report = _missing_context_report(root_dir)
        else:
            report = _run_discovery(
                model=model,
                root_dir=root_dir,
                messages=response_history(state["messages"]),
                runtime=runtime,
                agent_builder=agent_builder,
            )
        raise_if_cancelled(runtime)

        candidate = _primary_candidate(report)
        return {
            "discovery": report,
            "uncertainty": (
                candidate.uncertainty
                if candidate is not None
                else state["uncertainty"]
            ),
        }

    return discover


def route_discovery_result(state: ArchHypoState) -> DiscoveryRoute:
    """Continue to ArchHypo only when discovery found a candidate."""

    report = state.get("discovery")
    if report is None:
        raise ValueError("uncertainty discovery is required")
    if report.status == "found" and report.candidates:
        return "hypothesis_formulation"
    return "direct_response_generation"


def _run_discovery(
    *,
    model: BaseChatModel,
    root_dir: Path,
    messages: list[Any],
    runtime: Runtime[RunContext] | None,
    agent_builder: Callable[..., Runnable[Any, Any]],
) -> UncertaintyDiscoveryReport:
    try:
        agent = agent_builder(model, root_dir=root_dir)
        child_config = _child_config(runtime)
        result = agent.invoke({"messages": messages}, child_config)
        raw_report = (
            result.get("structured_response")
            if isinstance(result, dict)
            else result
        )
        return UncertaintyDiscoveryReport.model_validate(raw_report)
    except Exception:
        logger.exception("Architectural uncertainty discovery failed")
        return UncertaintyDiscoveryReport(
            status="failed",
            summary="The attached workspace could not be investigated.",
            missing_information=["A successful read-only workspace investigation."],
        )


def _folder_context_path(runtime: Runtime[RunContext] | None) -> Path | None:
    if runtime is None or not isinstance(runtime.context, dict):
        return None
    value = runtime.context.get("folder_context_path")
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value)


def _child_config(runtime: Runtime[RunContext] | None) -> dict[str, Any] | None:
    if runtime is None or not isinstance(runtime.context, dict):
        return None
    thread_id = runtime.context.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        return None
    return {"configurable": {"thread_id": thread_id}}


def _primary_candidate(report: UncertaintyDiscoveryReport):
    if report.status != "found" or not report.candidates:
        return None
    return report.candidates[0]


def _missing_context_report(root_dir: Path | None) -> UncertaintyDiscoveryReport:
    if root_dir is None:
        summary = "No folder is attached to this conversation."
    else:
        summary = "The attached folder is no longer available."
    return UncertaintyDiscoveryReport(
        status="insufficient_context",
        summary=summary,
        missing_information=["An accessible attached workspace."],
    )


__all__ = [
    "DiscoveryRoute",
    "create_uncertainty_discovery_node",
    "route_discovery_result",
]
