import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from archwise_agent.agents.hypothesis_formulator import (
    build_hypothesis_formulator_agent,
)
from archwise_agent.agents.orchestrator.nodes import (
    create_archwise_result_rendering_node,
    create_hypothesis_assessment_node,
    create_hypothesis_formulation_node,
    create_technical_plan_generation_node,
    create_uncertainty_discovery_node,
    route_discovery_result,
)
from archwise_agent.agents.orchestrator.nodes.uncertainty_discovery_node import (
    _DoomLoopGuard,
)
from archwise_agent.agents.technical_planner import build_technical_planner_agent
from archwise_agent.core import (
    ArchHypo,
    Hypothesis,
    HypothesisClassification,
    TechnicalPlan,
    UncertaintyDiscoveryReport,
)
from tests.fakes import archhypo_json, fake_hypothesis_model


def test_archwise_result_rendering_is_deterministic() -> None:
    node = create_archwise_result_rendering_node()
    result = ArchHypo.model_validate(
        json.loads(
            archhypo_json(
                "Peak capacity is unknown.",
                "The system handles the projected load.",
            )
        )
    )

    rendered = node({"result": result})

    assert rendered["response"].startswith("## ArchWise analysis")
    assert "### Classification" in rendered["response"]
    assert "### Technical plan" in rendered["response"]
    assert "messages" not in rendered


def test_formulate_hypothesis_node_normalizes_uncertainty() -> None:
    node = create_hypothesis_formulation_node(
        build_hypothesis_formulator_agent(
            fake_hypothesis_model(
                ["The system handles the load."],
                uncertainties=["Peak capacity is unknown."],
            )
        )
    )

    result = node({"uncertainty": "A long source document."})

    assert result["uncertainty"] == "Peak capacity is unknown."
    assert isinstance(result["hypothesis"], Hypothesis)
    assert result["messages"][0].name == "hypothesis_formulator_agent"


def test_doom_loop_guard_stops_the_fourth_consecutive_repeat() -> None:
    guard = _DoomLoopGuard()

    for index in range(3):
        call_id = f"ls-{index}"
        assert guard.accept(
            {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "ls",
                                "args": {"path": "/src"},
                                "id": call_id,
                            }
                        ],
                    )
                ]
            }
        )
        assert guard.accept(
            {
                "messages": [
                    ToolMessage(
                        content="['/src/app.py']",
                        tool_call_id=call_id,
                    )
                ]
            }
        )

    assert not guard.accept(
        {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "ls",
                            "args": {"path": "/src"},
                            "id": "ls-4",
                        }
                    ],
                )
            ]
        }
    )


def test_uncertainty_discovery_node_returns_a_candidate(tmp_path) -> None:
    report = UncertaintyDiscoveryReport.model_validate(
        {
            "status": "found",
            "summary": "The repository has an unclear integration boundary.",
            "candidates": [
                {
                    "uncertainty": "It is unclear who owns integration retries.",
                    "rationale": "Two components implement retry behavior.",
                }
            ],
            "evidence": [
                {
                    "path": "src/client.py",
                    "location": "Client.send",
                    "source_type": "code",
                    "observation": "The client retries failed requests.",
                }
            ],
            "confidence": 0.9,
        }
    )

    def build_fake_agent(*args, **kwargs):
        return RunnableLambda(lambda _: {"structured_response": report})

    node = create_uncertainty_discovery_node(
        model=fake_hypothesis_model(["unused"]),
        agent_builder=build_fake_agent,
    )
    runtime = SimpleNamespace(
        context={
            "thread_id": "discovery-thread",
            "folder_context_path": str(tmp_path),
        },
        control=SimpleNamespace(drain_requested=False),
    )

    result = node(
        {
            "messages": [HumanMessage(content="Investigate the repository.")],
            "uncertainty": "Investigate the repository.",
        },
        runtime,
    )

    assert result["discovery"] == report
    assert result["uncertainty"] == (
        "It is unclear who owns integration retries."
    )
    assert route_discovery_result({"discovery": report}) == (
        "hypothesis_formulation"
    )


def test_uncertainty_discovery_without_folder_goes_to_direct_response() -> None:
    node = create_uncertainty_discovery_node(
        model=fake_hypothesis_model(["unused"]),
    )

    result = node(
        {
            "messages": [HumanMessage(content="Investigate the repository.")],
            "uncertainty": "Investigate the repository.",
        }
    )

    report = result["discovery"]
    assert report.status == "insufficient_context"
    assert route_discovery_result(result) == "direct_response_generation"


def test_classify_hypothesis_node_requires_a_hypothesis() -> None:
    node = create_hypothesis_assessment_node(
        RunnableLambda(
            lambda _: HypothesisClassification(
                nfr="Performance",
                nfr_justification="Capacity.",
                impact="High",
                impact_justification="Important.",
                uncertainty="High",
                uncertainty_justification="Unknown.",
            )
        )
    )

    with pytest.raises(ValueError, match="hypothesis is required"):
        node({"uncertainty": "Peak capacity is unknown."})


def test_technical_plan_node_requires_previous_results() -> None:
    node = create_technical_plan_generation_node(RunnableLambda(lambda _: {}))

    with pytest.raises(
        ValueError,
        match="hypothesis and classification are required",
    ):
        node({"uncertainty": "Peak capacity is unknown."})


def test_technical_plan_node_builds_complete_result() -> None:
    model = fake_hypothesis_model(["unused"])
    hypothesis = Hypothesis(
        uncertainty="Peak capacity is unknown.",
        title="Peak capacity",
        statement="The system handles the projected load.",
        justification="It can be tested.",
    )
    classification = HypothesisClassification(
        nfr="Performance",
        nfr_justification="Capacity.",
        impact="High",
        impact_justification="Important.",
        uncertainty="High",
        uncertainty_justification="Unknown.",
    )
    node = create_technical_plan_generation_node(
        build_technical_planner_agent(model)
    )

    result = node(
        {
            "uncertainty": hypothesis.uncertainty,
            "hypothesis": hypothesis,
            "classification": classification,
        }
    )

    assert isinstance(result["technical_plan"], TechnicalPlan)
    assert result["result"].hypothesis == hypothesis
