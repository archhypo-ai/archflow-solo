from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda

from archwise_agent.agents.request_router import build_jev_request_router
from archwise_agent.config import AgentSettings
from archwise_agent.core import RequestRouting
from archwise_agent.providers import (
    JevDecisionResponse,
    JevError,
)


class FakeJevClient:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.state = None
        self.questions = None

    def decide(self, *, state, questions):
        self.state = state
        self.questions = questions
        if self.error is not None:
            raise self.error
        return self.response


def configuration() -> AgentSettings:
    return AgentSettings(_env_file=None, openrouter_api_key="test-key")


def test_jev_request_router_maps_choice_to_request_routing() -> None:
    client = FakeJevClient(
        response=JevDecisionResponse.model_validate(
            {
                "model": "typesafe/jev-1.13",
                "answers": {
                    "route": {
                        "type": "choice",
                        "choice": "archwise_workflow",
                        "confidence": 0.98,
                        "probabilities": {
                            "archwise_workflow": 0.99,
                            "direct_response": 0.01,
                        },
                    }
                },
            }
        )
    )
    fallback = RunnableLambda(
        lambda _: RequestRouting(route="direct_response")
    )
    router = build_jev_request_router(
        configuration=configuration(),
        fallback_agent=fallback,
        client=client,
    )

    result = router.invoke({"messages": [HumanMessage(content="Analyze this.")]})

    assert result == RequestRouting(
        route="archwise_workflow",
        confidence=0.98,
        probabilities={
            "archwise_workflow": 0.99,
            "direct_response": 0.01,
        },
    )
    assert result.probabilities == {
        "archwise_workflow": 0.99,
        "direct_response": 0.01,
    }
    assert client.state == "Analyze this."
    assert "route" in client.questions


def test_jev_request_router_falls_back_to_llm() -> None:
    client = FakeJevClient(error=JevError("provider unavailable"))
    fallback = RunnableLambda(
        lambda _: RequestRouting(route="direct_response")
    )
    router = build_jev_request_router(
        configuration=configuration(),
        fallback_agent=fallback,
        client=client,
    )

    result = router.invoke({"messages": [HumanMessage(content="Hello.")]})

    assert result == RequestRouting(route="direct_response")
