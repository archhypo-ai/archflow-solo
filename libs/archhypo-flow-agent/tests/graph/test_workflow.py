from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage

from archhypo_flow_agent.graph import build_graph
from tests.fakes import StructuredOutputStub


class StubModel(StructuredOutputStub, FakeListChatModel):
    def __init__(self) -> None:
        super().__init__(responses=["Hello from the test agent."])

    def bind_tools(self, tools, **kwargs):
        return self


def test_graph_runs_the_minimum_archhypo_path_before_responding() -> None:
    graph = build_graph(model=StubModel())

    result = graph.invoke({"messages": [HumanMessage(content="Hello")]})

    assert result["messages"][-1].content == "Hello from the test agent."
    assert result["routing"].route == "architectural_uncertainty_discovery"
    assert result["discovery"].uncertainty == "Hello"
    assert result["hypothesis"].statement
    assert result["assessment"].impact == "Medium"
    assert result["technical_plan"].items[0].pattern == "Architectural Spike"
    graph_diagram = graph.get_graph().draw_mermaid()
    stages = [
        "request_routing",
        "architectural_uncertainty_discovery",
        "hypothesis_formulation",
        "hypothesis_assessment",
        "technical_plan_generation",
        "response_generation",
    ]
    assert all(stage in graph_diagram for stage in stages)
    assert set(graph.get_graph().nodes) == {
        "__start__",
        "__end__",
        *stages,
    }
