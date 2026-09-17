from archwise_agent import HypothesisClassification, build_classifier_agent
from archwise_agent.agents.classifier.agent import classifier_input
from tests.fakes import fake_hypothesis_model


def test_classifier_agent_returns_fixed_pydantic_output() -> None:
    agent = build_classifier_agent(fake_hypothesis_model(["unused"]))

    result = agent.invoke(
        classifier_input(
            "It is uncertain whether the system meets peak load.",
            '{"statement":"The system handles the projected peak load."}',
        )
    )

    assert isinstance(result, HypothesisClassification)
    assert result.nfr == "Performance"
    assert result.impact == "High"
    assert result.uncertainty == "High"
