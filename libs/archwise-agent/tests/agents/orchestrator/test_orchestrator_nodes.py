import json

import pytest
from langchain_core.runnables import RunnableLambda

from archwise_agent.agents.hypothesis_formulator import (
    build_hypothesis_formulator_agent,
)
from archwise_agent.agents.orchestrator.nodes import (
    create_archwise_result_rendering_node,
    create_hypothesis_assessment_node,
    create_hypothesis_formulation_node,
    create_technical_plan_generation_node,
)
from archwise_agent.agents.technical_planner import build_technical_planner_agent
from archwise_agent.core import (
    ArchHypo,
    Hypothesis,
    HypothesisClassification,
    TechnicalPlan,
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
