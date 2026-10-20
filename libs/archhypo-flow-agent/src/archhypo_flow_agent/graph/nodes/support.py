"""Shared helpers for the structured workflow nodes."""

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_contextual_system_prompt
from archhypo_flow_agent.core import AgentRunContext, AgentState


def latest_user_input(messages: list[Any]) -> str:
    """Return the newest human message as plain text."""

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                return content
            return "\n".join(
                str(block["text"])
                for block in content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            )
    raise ValueError("a user message is required to run ArchHypo stages")


def contextual_system_prompt(
    base_prompt: str,
    runtime: Runtime[AgentRunContext] | None,
) -> str:
    context = runtime.context if runtime is not None else None
    return build_contextual_system_prompt(base_prompt, context)


def human_review_enabled(runtime: Runtime[AgentRunContext] | None) -> bool:
    """Require human review unless the run context explicitly disables it."""

    context = runtime.context if runtime is not None else None
    return context.get("hitl_enabled", True) if isinstance(context, dict) else True


def analysis_context(state: AgentState) -> dict[str, object]:
    """Return a bounded structured summary for router and direct-answer nodes."""

    return {
        "active_result": _jsonable(state.get("result")),
        "active_uncertainty": state.get("uncertainty"),
        "active_hypothesis": _jsonable(state.get("hypothesis")),
        "previous_results": [
            _jsonable(result) for result in state.get("result_history", [])[-5:]
        ],
    }


def _jsonable(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


__all__ = [
    "analysis_context",
    "contextual_system_prompt",
    "human_review_enabled",
    "latest_user_input",
]
