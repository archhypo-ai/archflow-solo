from archwise_agent import HypothesisClassification
from archwise_agent.agents.hypothesis_assessor import (
    build_hypothesis_assessor_agent,
)
from archwise_agent.agents.hypothesis_assessor.hypothesis_assessor_agent import (
    make_hypothesis_assessment_input,
)
from tests.fakes import fake_hypothesis_model


def test_hypothesis_assessor_returns_fixed_pydantic_output() -> None:
    agent = build_hypothesis_assessor_agent(fake_hypothesis_model(["unused"]))

    result = agent.invoke(
        make_hypothesis_assessment_input(
            "It is uncertain whether the system meets peak load.",
            '{"statement":"The system handles the projected peak load."}',
        )
    )

    assert isinstance(result, HypothesisClassification)
    assert result.nfr == "Performance"
    assert result.impact == "High"
    assert result.uncertainty == "High"
