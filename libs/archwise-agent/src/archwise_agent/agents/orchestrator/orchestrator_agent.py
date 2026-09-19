"""ArchWise workflow orchestrator."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from archwise_agent.agents.hypothesis_assessor import (
    build_hypothesis_assessor_agent,
)
from archwise_agent.agents.hypothesis_formulator import (
    build_hypothesis_formulator_agent,
)
from archwise_agent.agents.request_router import build_request_router_agent
from archwise_agent.agents.response_composer import build_response_composer_agent
from archwise_agent.agents.technical_planner import build_technical_planner_agent
from archwise_agent.config import AgentSettings
from archwise_agent.core import ArchHypoState, RunContext
from archwise_agent.providers import create_openrouter_model

from .nodes import (
    create_archwise_response_generation_node,
    create_archwise_result_rendering_node,
    create_direct_response_generation_node,
    create_hypothesis_assessment_node,
    create_hypothesis_formulation_node,
    create_request_routing_node,
    create_technical_plan_generation_node,
    route_request,
)


def build_orchestrator_agent(
    *,
    model: BaseChatModel | None = None,
    configuration: AgentSettings | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build and compile the ArchHypo workflow orchestrator."""

    chat_model = model or create_openrouter_model(configuration)
    request_router_agent = build_request_router_agent(chat_model)
    response_composer_agent = build_response_composer_agent(chat_model)
    hypothesis_formulator_agent = build_hypothesis_formulator_agent(chat_model)
    hypothesis_assessor_agent = build_hypothesis_assessor_agent(chat_model)
    technical_planner_agent = build_technical_planner_agent(chat_model)

    workflow = StateGraph(ArchHypoState, context_schema=RunContext)
    workflow.add_node(
        "request_routing",
        create_request_routing_node(request_router_agent),
    )
    workflow.add_node(
        "direct_response_generation",
        create_direct_response_generation_node(response_composer_agent),
    )
    workflow.add_node(
        "archwise_result_rendering",
        create_archwise_result_rendering_node(),
    )
    workflow.add_node(
        "archwise_response_generation",
        create_archwise_response_generation_node(response_composer_agent),
    )
    workflow.add_node(
        "hypothesis_formulation",
        create_hypothesis_formulation_node(hypothesis_formulator_agent),
    )
    workflow.add_node(
        "hypothesis_assessment",
        create_hypothesis_assessment_node(hypothesis_assessor_agent),
    )
    workflow.add_node(
        "technical_plan_generation",
        create_technical_plan_generation_node(technical_planner_agent),
    )

    workflow.add_edge(START, "request_routing")
    workflow.add_conditional_edges(
        "request_routing",
        route_request,
        {
            "direct_response_generation": "direct_response_generation",
            "hypothesis_formulation": "hypothesis_formulation",
        },
    )
    workflow.add_edge("direct_response_generation", END)
    workflow.add_edge("hypothesis_formulation", "hypothesis_assessment")
    workflow.add_edge("hypothesis_assessment", "technical_plan_generation")
    workflow.add_edge(
        "technical_plan_generation",
        "archwise_result_rendering",
    )
    workflow.add_edge(
        "archwise_result_rendering",
        "archwise_response_generation",
    )
    workflow.add_edge("archwise_response_generation", END)

    return workflow.compile(
        checkpointer=(checkpointer if checkpointer is not None else InMemorySaver())
    )


__all__ = ["build_orchestrator_agent"]
