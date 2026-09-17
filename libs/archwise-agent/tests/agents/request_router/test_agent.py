from langchain_core.messages import HumanMessage

from archwise_agent import RequestRouting, build_request_router_agent
from tests.fakes import fake_hypothesis_model


def test_request_router_can_answer_directly() -> None:
    agent = build_request_router_agent(
        fake_hypothesis_model(
            ["unused"],
            route="direct_response",
            direct_response="Tirana.",
        )
    )

    result = agent.invoke(
        {"messages": [HumanMessage(content="What is the capital of Albania?")]}
    )

    assert result == RequestRouting(route="direct_response")


def test_request_router_can_select_the_archwise_workflow() -> None:
    agent = build_request_router_agent(fake_hypothesis_model(["unused"]))

    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Analyze whether the architecture handles peak load."
                )
            ]
        }
    )

    assert result == RequestRouting(route="archwise_workflow")
