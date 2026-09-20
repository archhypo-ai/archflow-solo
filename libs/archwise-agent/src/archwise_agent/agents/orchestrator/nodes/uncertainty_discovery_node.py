"""Workflow node for discovering architectural uncertainty in an attachment."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable
from langgraph.errors import GraphRecursionError
from langgraph.runtime import Runtime

from archwise_agent.agents.uncertainty_discovery import (
    build_uncertainty_discovery_agent,
)
from archwise_agent.core import (
    ArchHypoState,
    RunContext,
    UncertaintyDiscoveryReport,
)
from archwise_agent.graph import (
    GraphNode,
    raise_if_cancelled,
    stream_agent_with_tool_events,
)

from .direct_response_generation_node import response_history

logger = logging.getLogger(__name__)

DiscoveryRoute = Literal[
    "hypothesis_formulation",
    "direct_response_generation",
]

_PARTIAL_DISCOVERY_PROMPT = """\
The read-only workspace investigation was stopped because the agent made
three consecutive identical tool calls. Produce the final structured
discovery report now, using only the user request and the tool results already
present in the conversation. Do not call tools. Treat the attached workspace
as partial and return a concrete candidate when the observed evidence supports
one. Return insufficient_context only when the available evidence truly
cannot support a candidate. Do not invent facts or ask for the repository
path: the workspace was already attached.
"""


class _DoomLoopGuard:
    """Stop three consecutive identical completed read calls before the fourth."""

    threshold = 3

    def __init__(self) -> None:
        self._pending_calls: dict[str, str] = {}
        self._recent_completed: list[str] = []
        self._seen_message_ids: set[str] = set()
        self._seen_message_objects: list[Any] = []

    def accept(self, update: Any) -> bool:
        for message in _update_messages(update):
            message_id = getattr(message, "id", None)
            if isinstance(message_id, str):
                if message_id in self._seen_message_ids:
                    continue
                self._seen_message_ids.add(message_id)
            else:
                if any(existing is message for existing in self._seen_message_objects):
                    continue
                self._seen_message_objects.append(message)

            if isinstance(message, AIMessage):
                for call in message.tool_calls:
                    call_id = call.get("id")
                    signature = _tool_call_signature(call)
                    if (
                        len(self._recent_completed) >= self.threshold
                        and all(
                            item == signature
                            for item in self._recent_completed[-self.threshold :]
                        )
                    ):
                        return False
                    if isinstance(call_id, str):
                        self._pending_calls[call_id] = signature
            elif isinstance(message, ToolMessage):
                call_id = message.tool_call_id
                if isinstance(call_id, str):
                    signature = self._pending_calls.pop(call_id, None)
                    if signature is not None:
                        self._recent_completed.append(signature)
                        del self._recent_completed[:-self.threshold]
        return True


def _tool_call_signature(call: dict[str, Any]) -> str:
    return json.dumps(
        {
            "name": call.get("name"),
            "args": call.get("args", {}),
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )


def _update_messages(update: Any) -> Iterator[Any]:
    if not isinstance(update, dict):
        return
    messages = update.get("messages")
    if isinstance(messages, list):
        yield from messages
    for value in update.values():
        if isinstance(value, dict):
            yield from _update_messages(value)


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
        guard = _DoomLoopGuard()
        result = stream_agent_with_tool_events(
            agent,
            {"messages": messages},
            config=child_config,
            runtime=runtime,
            on_update=guard.accept,
        )
        if isinstance(result, dict) and result.get("stopped"):
            return _finalize_partial_discovery(
                model,
                messages,
                result.get("messages", []),
            )
        raw_report = (
            result.get("structured_response")
            if isinstance(result, dict)
            else result
        )
        return UncertaintyDiscoveryReport.model_validate(raw_report)
    except GraphRecursionError:
        logger.warning(
            "Architectural uncertainty discovery reached its emergency recursion limit"
        )
        return UncertaintyDiscoveryReport(
            status="insufficient_context",
            summary=(
                "The investigation was stopped before it could produce a final "
                "report. Use the evidence already collected and request only "
                "the missing context if necessary."
            ),
            missing_information=[
                "A final structured discovery report from the attached workspace."
            ],
        )
    except Exception:
        logger.exception("Architectural uncertainty discovery failed")
        return UncertaintyDiscoveryReport(
            status="failed",
            summary="The attached workspace could not be investigated.",
            missing_information=["A successful read-only workspace investigation."],
        )


def _finalize_partial_discovery(
    model: BaseChatModel,
    user_messages: list[Any],
    investigation_messages: list[Any],
) -> UncertaintyDiscoveryReport:
    """Finish from collected read results after a repeated-call loop."""

    finalizer = model.with_structured_output(UncertaintyDiscoveryReport)
    result = finalizer.invoke(
        [
            SystemMessage(content=_PARTIAL_DISCOVERY_PROMPT),
            *user_messages,
            *investigation_messages,
            HumanMessage(
                content=(
                    "Finalize the discovery report from the evidence above. "
                    "Do not perform another workspace lookup."
                )
            ),
        ]
    )
    return UncertaintyDiscoveryReport.model_validate(result)


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
