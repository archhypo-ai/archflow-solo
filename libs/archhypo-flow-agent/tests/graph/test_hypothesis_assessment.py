from unittest.mock import Mock

import pytest
from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from archhypo_flow_agent.core import (
    AgentState,
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    StructuredOutputError,
)
from archhypo_flow_agent.graph.nodes import hypothesis_assessment


def assessment() -> HypothesisAssessment:
    return HypothesisAssessment(
        nfr="Performance",
        nfr_justification="The concern is about handling projected throughput.",
        impact="High",
        impact_justification="The deployment decision affects peak capacity.",
        uncertainty="Medium",
        uncertainty_justification="The peak load is projected but unmeasured.",
    )


def missing_uncertainty_justification_error() -> ValidationError:
    fields = assessment().model_dump()
    fields.pop("uncertainty_justification")
    with pytest.raises(ValidationError) as raised:
        HypothesisAssessment.model_validate(fields)
    return raised.value


def assessment_state() -> AgentState:
    uncertainty = "Can one server sustain the projected peak ingestion rate?"
    return {
        "messages": [HumanMessage(content=uncertainty)],
        "uncertainty": uncertainty,
        "discovery": ArchitecturalUncertaintyDiscovery(
            status="identified",
            uncertainty=uncertainty,
            rationale="The user described an unresolved capacity decision.",
        ),
        "hypothesis": Hypothesis(
            uncertainty=uncertainty,
            title="Single server capacity",
            statement="A single server can sustain the projected peak rate.",
            justification="This is measurable against the expected throughput.",
        ),
    }


def test_assessment_retries_once_with_missing_field_feedback(monkeypatch) -> None:
    agent = Mock()
    agent.invoke.side_effect = [missing_uncertainty_justification_error(), assessment()]
    monkeypatch.setattr(
        hypothesis_assessment,
        "build_hypothesis_assessment_agent",
        lambda _model: agent,
    )
    node = hypothesis_assessment.create_hypothesis_assessment_node(Mock())

    update = node(assessment_state())

    assert update["assessment"] == assessment()
    assert agent.invoke.call_count == 2
    assert agent.invoke.call_args_list[0].args[0]["repair_feedback"] == ""
    assert "uncertainty_justification" in agent.invoke.call_args_list[1].args[0][
        "repair_feedback"
    ]


def test_assessment_raises_safe_error_after_retry_also_fails(monkeypatch) -> None:
    error = missing_uncertainty_justification_error()
    agent = Mock()
    agent.invoke.side_effect = [error, error]
    monkeypatch.setattr(
        hypothesis_assessment,
        "build_hypothesis_assessment_agent",
        lambda _model: agent,
    )
    node = hypothesis_assessment.create_hypothesis_assessment_node(Mock())

    with pytest.raises(StructuredOutputError) as raised:
        node(assessment_state())

    assert raised.value.stage == "hypothesis_assessment"
    assert raised.value.attempts == 2
    assert agent.invoke.call_count == 2
