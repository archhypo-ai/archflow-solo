from archwise_agent import Hypothesis
from archwise_agent.agents.hypothesis_formulator import (
    build_hypothesis_formulator_agent,
)
from archwise_agent.agents.hypothesis_formulator.hypothesis_formulator_agent import (
    make_hypothesis_input,
)
from tests.fakes import fake_hypothesis_model


def test_hypothesis_formulator_returns_fixed_pydantic_output() -> None:
    agent = build_hypothesis_formulator_agent(
        fake_hypothesis_model(
            ["Redis can keep p95 read latency below the required limit."],
            uncertainties=[
                "It is uncertain whether Redis meets the read latency requirement."
            ],
        )
    )

    result = agent.invoke(
        make_hypothesis_input("Can Redis satisfy the read latency requirement?")
    )

    assert isinstance(result, Hypothesis)
    assert result.uncertainty == (
        "It is uncertain whether Redis meets the read latency requirement."
    )
    assert result.statement == (
        "Redis can keep p95 read latency below the required limit."
    )
