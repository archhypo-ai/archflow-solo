"""Application-facing invocation of the compiled conversational graph."""

from collections.abc import Sequence

from langchain_core.messages import AnyMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph


class AgentService:
    """Small adapter that keeps transport code independent of graph internals."""

    def __init__(self, graph: CompiledStateGraph) -> None:
        self._graph = graph

    def respond(
        self,
        messages: Sequence[AnyMessage],
        *,
        config: RunnableConfig | None = None,
    ) -> BaseMessage:
        """Run the graph with supplied conversation messages and return its reply."""

        result = self._graph.invoke(
            {"messages": list(messages)},
            config=config,
        )
        return result["messages"][-1]


__all__ = ["AgentService"]
