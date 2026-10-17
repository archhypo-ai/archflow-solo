"""LangGraph workflow for routed ArchHypo and conversational responses."""

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from archhypo_flow_agent.agents import (
    build_direct_response_agent,
    build_response_generation_agent,
)
from archhypo_flow_agent.core import AgentRunContext, AgentState
from archhypo_flow_agent.graph.nodes import (
    create_architectural_uncertainty_discovery_node,
    create_direct_response_generation_node,
    create_hypothesis_assessment_node,
    create_hypothesis_formulation_node,
    create_request_routing_node,
    create_response_generation_node,
    create_technical_plan_generation_node,
    hypothesis_review_node,
    route_after_hypothesis_review,
    route_after_technical_plan_review,
    route_request,
    technical_plan_review_node,
)
from archhypo_flow_agent.providers import SystemOneClient


def build_graph(
    model: BaseChatModel,
    *,
    tools: Sequence[BaseTool] = (),
    checkpointer: BaseCheckpointSaver | None = None,
    system_one_client: SystemOneClient | None = None,
):
    """Build the routed direct-response and ArchHypo workflows.

    SystemOne is injected when configured; the router has a structured LLM
    fallback. Direct and final responses use separate prompts. A checkpointer
    may be injected by the application; it is required to resume human review.
    Graph construction owns no storage.
    """

    response_agent = build_response_generation_agent(
        model,
        tools=tools,
    )
    workflow = StateGraph(AgentState, context_schema=AgentRunContext)
    workflow.add_node(
        "request_routing",
        create_request_routing_node(model, system_one_client=system_one_client),
    )
    workflow.add_node(
        "direct_response_generation",
        create_direct_response_generation_node(
            build_direct_response_agent(model, tools=tools)
        ),
    )
    workflow.add_node(
        "architectural_uncertainty_discovery",
        create_architectural_uncertainty_discovery_node(model),
    )
    workflow.add_node(
        "hypothesis_formulation",
        create_hypothesis_formulation_node(model),
    )
    workflow.add_node(
        "hypothesis_assessment",
        create_hypothesis_assessment_node(model),
    )
    workflow.add_node("hypothesis_review", hypothesis_review_node)
    workflow.add_node(
        "technical_plan_generation",
        create_technical_plan_generation_node(model),
    )
    workflow.add_node("technical_plan_review", technical_plan_review_node)
    workflow.add_node(
        "response_generation",
        create_response_generation_node(response_agent),
    )
    workflow.add_edge(START, "request_routing")
    workflow.add_conditional_edges(
        "request_routing",
        route_request,
        {
            "architectural_uncertainty_discovery": (
                "architectural_uncertainty_discovery"
            ),
            "hypothesis_formulation": "hypothesis_formulation",
            "direct_response_generation": "direct_response_generation",
        },
    )
    workflow.add_edge("direct_response_generation", END)
    workflow.add_edge("architectural_uncertainty_discovery", "hypothesis_formulation")
    workflow.add_edge("hypothesis_formulation", "hypothesis_review")
    workflow.add_conditional_edges(
        "hypothesis_review",
        route_after_hypothesis_review,
        {
            "hypothesis_assessment": "hypothesis_assessment",
            "hypothesis_formulation": "hypothesis_formulation",
        },
    )
    workflow.add_edge("hypothesis_assessment", "technical_plan_generation")
    workflow.add_edge("technical_plan_generation", "technical_plan_review")
    workflow.add_conditional_edges(
        "technical_plan_review",
        route_after_technical_plan_review,
        {
            "response_generation": "response_generation",
            "technical_plan_generation": "technical_plan_generation",
        },
    )
    workflow.add_edge("response_generation", END)
    return workflow.compile(checkpointer=checkpointer)


__all__ = ["build_graph"]
