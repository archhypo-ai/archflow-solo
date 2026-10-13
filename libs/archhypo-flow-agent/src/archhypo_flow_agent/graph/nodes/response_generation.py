"""Final response node that reuses the existing conversational agent."""

from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archhypo_flow_agent.core import AgentRunContext, AgentState


def create_response_generation_node(response_agent: Runnable[Any, Any]):
    def respond(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        result = state.get("result")
        if result is None:
            raise ValueError("an ArchHypo result is required before responding")

        existing_messages = state["messages"]
        result_prompt = HumanMessage(
            content=(
                "Explain the following ArchHypo result in the same language as "
                "the latest user request. Use it as the source of truth; make "
                "the uncertainty, hypothesis, assessment, and plan clear. "
                "Do not claim that documents or code were inspected.\n\n"
                f"{result.model_dump_json(indent=2)}"
            )
        )
        invoke_kwargs: dict[str, object] = {}
        if runtime is not None:
            invoke_kwargs["context"] = runtime.context
        response = response_agent.invoke(
            {"messages": [*existing_messages, result_prompt]},
            **invoke_kwargs,
        )
        response_messages = (
            response.get("messages") if isinstance(response, dict) else None
        )
        if not isinstance(response_messages, list):
            raise ValueError("response agent returned no messages")

        # Do not persist the synthetic result prompt as a user-visible message.
        prompt_index = next(
            (
                index
                for index, message in enumerate(response_messages)
                if isinstance(message, HumanMessage)
                and message.content == result_prompt.content
            ),
            None,
        )
        if prompt_index is not None:
            new_messages = response_messages[prompt_index + 1 :]
        elif response_messages[: len(existing_messages)] == existing_messages:
            new_messages = response_messages[len(existing_messages) :]
        else:
            new_messages = response_messages
        if not new_messages:
            raise ValueError(
                "response agent returned no final response "
                f"({len(response_messages)} messages, prompt index {prompt_index}, "
                f"{len(existing_messages)} prior messages)"
            )
        return {"messages": new_messages}

    return respond


__all__ = ["create_response_generation_node"]
