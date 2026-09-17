from archwise_agent import Hypothesis, build_hypothesis_agent
from archwise_agent.agents.hypothesis.agent import hypothesis_input
from tests.fakes import fake_hypothesis_model


def test_hypothesis_agent_returns_fixed_pydantic_output() -> None:
    agent = build_hypothesis_agent(
        fake_hypothesis_model(
            ["Redis can keep p95 read latency below the required limit."],
            uncertainties=[
                "It is uncertain whether Redis meets the read latency requirement."
            ],
        )
    )

    result = agent.invoke(
        hypothesis_input("Can Redis satisfy the read latency requirement?")
    )

    assert isinstance(result, Hypothesis)
    assert result.uncertainty == (
        "It is uncertain whether Redis meets the read latency requirement."
    )
    assert result.statement == (
        "Redis can keep p95 read latency below the required limit."
    )
