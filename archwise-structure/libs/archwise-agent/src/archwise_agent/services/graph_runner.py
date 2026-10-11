"""Execution adapter for the compiled ArchWise graph."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.runtime import RunControl

from archwise_agent.agents import build_orchestrator_agent
from archwise_agent.config import AgentSettings
from archwise_agent.core import ExecutionContext
from archwise_agent.observability import Observability


class GraphRunner:
    """Own graph construction and invoke it with consistent runtime config."""

    def __init__(
        self,
        *,
        model: BaseChatModel | None,
        configuration: AgentSettings,
        checkpointer: BaseCheckpointSaver,
        observability: Observability,
    ) -> None:
        self._agent = build_orchestrator_agent(
            model=model,
            configuration=configuration,
            checkpointer=checkpointer,
        )
        self._observability = observability

    def invoke(
        self,
        *,
        message: str,
        context: ExecutionContext,
        control: RunControl,
    ) -> dict[str, Any]:
        """Execute one message through the compiled graph."""

        config = self._observability.graph_config(context)
        # thread_id is the only configurable value used for checkpoint
        # persistence.  Per-execution data belongs in runtime context and
        # tracing, never in the conversation checkpoint key.
        config["configurable"] = {"thread_id": context.thread_id}
        return self._agent.invoke(
            {
                "uncertainty": message,
                "messages": [HumanMessage(content=message)],
            },
            config,
            context=context.as_graph_context(),
            control=control,
        )

    def stream(
        self,
        *,
        message: str,
        context: ExecutionContext,
        control: RunControl,
    ) -> Iterator[tuple[str, Any]]:
        """Stream graph values and custom nested-agent events."""

        config = self._observability.graph_config(context)
        config["configurable"] = {"thread_id": context.thread_id}
        yield from self._agent.stream(
            {
                "uncertainty": message,
                "messages": [HumanMessage(content=message)],
            },
            config,
            context=context.as_graph_context(),
            control=control,
            stream_mode=["values", "custom"],
        )

    def get_state(self, thread_id: str) -> Any:
        """Read the latest checkpoint state for a thread."""

        return self._agent.get_state({"configurable": {"thread_id": thread_id}})

    def list_checkpoints(self) -> list[Any]:
        """List checkpoints used to discover persisted conversations."""

        return list(self._agent.checkpointer.list(None))

    def delete_thread(self, thread_id: str) -> None:
        """Delete a thread when no shared persistence transaction is needed."""

        self._agent.checkpointer.delete_thread(thread_id)

    @property
    def agent(self):
        """Expose the compiled graph for compatibility and diagnostics."""

        return self._agent


__all__ = ["GraphRunner"]
