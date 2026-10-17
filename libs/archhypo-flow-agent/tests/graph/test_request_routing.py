from unittest.mock import Mock

import pytest
from langchain_core.messages import HumanMessage

from archhypo_flow_agent.core import AgentState
from archhypo_flow_agent.graph.nodes import create_request_routing_node
from archhypo_flow_agent.providers import (
    SystemOneClient,
    SystemOneRequestError,
    SystemOneResponse,
    SystemOneResponseError,
)
from tests.fakes import StubSystemOneClient


def test_router_requires_a_system_one_client() -> None:
    with pytest.raises(ValueError, match="SystemOne client is required"):
        create_request_routing_node(None)


def test_routing_failure_propagates_without_a_default_route() -> None:
    error = SystemOneRequestError("decision service unavailable")
    client = StubSystemOneClient(error=error)
    route = create_request_routing_node(client)
    state: AgentState = {"messages": [HumanMessage(content="Explain ArchHypo")]}

    with pytest.raises(SystemOneRequestError) as raised:
        route(state)

    assert raised.value is error
    assert client.calls == 1
    assert "routing" not in state
    assert "hypothesis" not in state


@pytest.mark.parametrize(
    "answers",
    [
        {},
        {"intent": {"type": "choice", "choice": "unknown"}},
        {"intent": {"type": "choice"}},
        {"intent": {"type": "score", "choice": "contextual_question"}},
    ],
)
def test_invalid_decision_stops_routing_without_fallback(answers) -> None:
    client = Mock(spec=SystemOneClient)
    client.decide.return_value = SystemOneResponse.model_validate(
        {"model": "test/decision-model", "answers": answers}
    )
    route = create_request_routing_node(client)
    state: AgentState = {"messages": [HumanMessage(content="Explain ArchHypo")]}

    with pytest.raises(SystemOneResponseError, match="invalid request intent"):
        route(state)

    client.decide.assert_called_once()
    assert "routing" not in state


def test_missing_alternative_target_requests_clarification() -> None:
    client = StubSystemOneClient("alternative_hypothesis")
    route = create_request_routing_node(client)
    state: AgentState = {"messages": [HumanMessage(content="Gere outra hipótese")]}

    update = route(state)

    assert client.calls == 1
    assert update["routing"].intent == "clarification"
    assert update["routing"].route == "direct_response_generation"
