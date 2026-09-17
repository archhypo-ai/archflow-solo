"""Presentation of graph state as an application turn."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from .contracts import AgentTurn
from .conversation_projection import archhypo_from_value, response_message


def present_turn(thread_id: str, state: dict[str, Any]) -> AgentTurn:
    """Convert graph output into the stable application response contract."""

    direct_response = state.get("response")
    if isinstance(direct_response, str) and direct_response.strip():
        result = state.get("result")
        archhypo = archhypo_from_value(result) if result is not None else None
        response = AIMessage(content=direct_response)
    else:
        archhypo = archhypo_from_value(state.get("result"))
        response = response_message(archhypo)

    return AgentTurn(thread_id=thread_id, message=response, result=archhypo)


__all__ = ["present_turn"]
