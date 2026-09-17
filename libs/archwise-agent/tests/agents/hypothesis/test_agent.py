from archwise_agent import Hypothesis, build_hypothesis_agent
from tests.fakes import fake_hypothesis_model


def test_hypothesis_agent_returns_fixed_pydantic_output() -> None:
    agent = build_hypothesis_agent(
        fake_hypothesis_model(
            ["Redis can keep p95 read latency below the required limit."]
        )
    )

    result = agent.invoke(
        {"uncertainty": "Can Redis satisfy the read latency requirement?"}
    )

    assert isinstance(result, Hypothesis)
    assert result.statement == (
        "Redis can keep p95 read latency below the required limit."
    )
