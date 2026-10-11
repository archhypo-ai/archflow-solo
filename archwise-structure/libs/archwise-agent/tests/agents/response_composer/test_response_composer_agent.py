from langchain_core.messages import HumanMessage

from archwise_agent import UserResponse
from archwise_agent.agents.response_composer import build_response_composer_agent
from tests.fakes import fake_hypothesis_model


def test_response_composer_returns_human_facing_text() -> None:
    agent = build_response_composer_agent(
        fake_hypothesis_model(
            ["unused"],
            route="direct_response",
            direct_response="Tirana.",
        )
    )

    result = agent.invoke(
        {"messages": [HumanMessage(content="What is the capital of Albania?")]}
    )

    assert result == UserResponse(message="Tirana.")
