"""Generate a direct conversational answer without running ArchHypo stages."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable
from langgraph.runtime import Runtime

from archhypo_flow_agent.core import AgentRunContext, AgentState

from .support import analysis_context


def create_direct_response_generation_node(response_agent: Runnable[Any, Any]):
    """Reuse the conversational agent without entering the ArchHypo stages."""

    def respond(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        question = state.get("formulation_question")
        if question:
            return {
                "messages": [AIMessage(content=question)],
                "formulation_question": None,
            }
        routing = state.get("routing")
        intent = routing.intent if routing is not None else "contextual_question"
        serialized_analysis = json.dumps(
            analysis_context(state),
            ensure_ascii=False,
            default=str,
        )
        reference_context = HumanMessage(
            content=(
                "<archhypo_reference_context>\n"
                f"intent: {intent}\n"
                f"analysis: {serialized_analysis}\n"
                "</archhypo_reference_context>"
            )
        )
        messages = [*state["messages"], reference_context]
        invoke_kwargs: dict[str, object] = {}
        if runtime is not None:
            invoke_kwargs["context"] = runtime.context
        response = response_agent.invoke(
            {"messages": messages},
            **invoke_kwargs,
        )
        response_messages = (
            response.get("messages") if isinstance(response, dict) else None
        )
        if not isinstance(response_messages, list):
            raise ValueError("direct response agent returned no messages")
        prompt_index = next(
            (
                index
                for index, message in enumerate(response_messages)
                if isinstance(message, HumanMessage)
                and message.content == reference_context.content
            ),
            None,
        )
        if prompt_index is not None:
            new_messages = response_messages[prompt_index + 1 :]
        elif response_messages[: len(messages)] == messages:
            new_messages = response_messages[len(messages) :]
        else:
            new_messages = response_messages
        if not new_messages:
            raise ValueError("direct response agent returned no final response")
        return {"messages": new_messages}

    return respond


__all__ = ["create_direct_response_generation_node"]
