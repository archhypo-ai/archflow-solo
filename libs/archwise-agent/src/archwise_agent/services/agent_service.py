"""Application-facing service for the ArchWise agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from archwise_agent.agents import build_archwise_agent
from archwise_agent.config import AgentSettings


@dataclass(frozen=True, slots=True)
class AgentTurn:
    """Assistant response returned by one agent turn."""

    thread_id: str
    message: AIMessage

    @property
    def text(self) -> str:
        content = self.message.content
        if isinstance(content, str):
            return content
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )


class AgentService:
    """Keep the compiled agent alive and provide a stable application API."""

    def __init__(
        self,
        *,
        configuration: AgentSettings | None = None,
        model: BaseChatModel | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self._agent = build_archwise_agent(
            model=model,
            configuration=configuration,
            checkpointer=checkpointer,
        )

    def send(self, *, thread_id: str, message: str) -> AgentTurn:
        """Send a message while preserving the supplied checkpoint thread."""

        if not thread_id.strip():
            raise ValueError("thread_id must not be empty")
        if not message.strip():
            raise ValueError("message must not be empty")

        result: dict[str, Any] = self._agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            {"configurable": {"thread_id": thread_id}},
        )
        response = result["messages"][-1]
        if not isinstance(response, AIMessage):
            raise TypeError("agent did not return an AI message")
        return AgentTurn(thread_id=thread_id, message=response)

    @property
    def agent(self):
        """Expose the compiled agent to future streaming/resume adapters."""

        return self._agent


__all__ = ["AgentService", "AgentTurn"]
