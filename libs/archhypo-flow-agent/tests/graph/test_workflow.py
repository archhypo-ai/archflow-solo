import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import ValidationError

from archhypo_flow_agent.core import (
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    HypothesisReview,
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
    graph = build_graph(model=StubModel(), checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "approved-hypothesis"}}

    paused = graph.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config,
    )

    assert paused["hypothesis"].statement
    assert paused.get("assessment") is None
    assert graph.get_state(config).tasks[0].interrupts[0].value["kind"] == (
        "hypothesis_review"
    )

    result = graph.invoke(
        Command(resume={"decision": "approved"}),
        config=config,
    )

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
        "hypothesis_review",
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


def test_rejected_hypothesis_is_reformulated_using_required_feedback() -> None:
    graph = build_graph(model=StubModel(), checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "rejected-hypothesis"}}
    initial = graph.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config,
    )
    first_statement = initial["hypothesis"].statement

    graph.invoke(
        Command(
            resume={
                "decision": "rejected",
                "reason": "Make the statement directly testable.",
            }
        ),
        config=config,
    )
    revised = graph.get_state(config).values["hypothesis"]

    assert revised.statement != first_statement
    assert "Make the statement directly testable." in revised.statement
    assert graph.get_state(config).values.get("assessment") is None

    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    assert graph.get_state(config).values["assessment"].impact == "Medium"


def test_rejection_requires_a_reason() -> None:
    with pytest.raises(ValidationError, match="reason is required"):
        HypothesisReview(decision="rejected")


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
