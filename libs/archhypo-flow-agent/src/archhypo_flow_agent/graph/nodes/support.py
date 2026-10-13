"""Shared helpers for the structured workflow nodes."""

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_contextual_system_prompt
from archhypo_flow_agent.core import AgentRunContext


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


__all__ = ["contextual_system_prompt", "latest_user_input"]
