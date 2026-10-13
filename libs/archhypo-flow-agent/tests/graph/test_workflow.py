import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage

from archhypo_flow_agent.core import (
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    TechnicalPlan,
)
from archhypo_flow_agent.graph import build_graph
from archhypo_flow_agent.graph.nodes import technical_plan_generation
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


def test_technical_plan_cannot_use_an_unread_catalog_pattern(monkeypatch) -> None:
    class InvalidPlanner:
        def invoke(self, _input):
            return TechnicalPlan(
                items=[
                    {
                        "title": "Trace the system",
                        "objective": "Collect evidence about behavior.",
                        "description": "Follow the behavior end to end.",
                        "pattern": "Tracer Bullets",
                        "tradeoff": "Requires a focused implementation effort.",
                    }
                ],
                rationale="A tracer bullet can gather evidence.",
            )

    monkeypatch.setattr(
        technical_plan_generation,
        "build_technical_plan_generation_agent",
        lambda _model: InvalidPlanner(),
    )
    node = technical_plan_generation.create_technical_plan_generation_node(
        StructuredOutputStub()
    )
    state = {
        "uncertainty": "The system behavior has not been validated.",
        "discovery": ArchitecturalUncertaintyDiscovery(
            status="identified",
            uncertainty="The system behavior has not been validated.",
            rationale="The user identified an unknown system behavior.",
        ),
        "hypothesis": Hypothesis(
            uncertainty="The system behavior has not been validated.",
            title="Validate system behavior",
            statement="The system meets the stated behavior.",
            justification="This is a testable statement.",
        ),
        "assessment": HypothesisAssessment(
            nfr="Reliability",
            nfr_justification="The concern relates to reliable behavior.",
            impact="Medium",
            impact_justification="Changing the architecture may require rework.",
            uncertainty="High",
            uncertainty_justification="The hypothesis has not been tested.",
        ),
    }

    with pytest.raises(ValueError, match="without reading their catalog references"):
        node(state)
