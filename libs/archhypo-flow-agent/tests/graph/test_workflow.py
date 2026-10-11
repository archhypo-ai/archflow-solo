from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage

from archhypo_flow_agent.graph import build_graph


class StubModel(FakeListChatModel):
    def __init__(self) -> None:
        super().__init__(responses=["Hello from the test agent."])

    def bind_tools(self, tools, **kwargs):
        return self


def test_graph_routes_conversation_to_response_generation() -> None:
    graph = build_graph(model=StubModel())

    result = graph.invoke({"messages": [HumanMessage(content="Hello")]})

    assert result["messages"][-1].content == "Hello from the test agent."
    assert "response_generation" in graph.get_graph().draw_mermaid()
