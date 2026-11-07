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
    create_artifact_persistence_node,
    create_direct_response_generation_node,
    create_hypothesis_assessment_node,
    create_hypothesis_formulation_node,
    create_request_routing_node,
    create_response_generation_node,
    create_technical_plan_generation_node,
    hypothesis_review_node,
    route_after_hypothesis_formulation,
    route_after_hypothesis_review,
    route_after_technical_plan_review,
    route_request,
    technical_plan_review_node,
)
from archhypo_flow_agent.graph.nodes.context_sufficiency import (
    create_context_sufficiency_node,
    route_after_discovery,
    route_after_sufficiency,
)
from archhypo_flow_agent.graph.nodes.documentary_research import (
    create_documentary_research_node,
    route_entry,
)
from archhypo_flow_agent.persistence import ArchHypoArtifactRepository
from archhypo_flow_agent.providers import SystemOneClient


def build_graph(
    model: BaseChatModel,
    *,
    system_one_client: SystemOneClient,
    artifact_repository: ArchHypoArtifactRepository,
    chat_model_id: str | None = None,
    system_one_model_id: str | None = None,
    tools: Sequence[BaseTool] = (),
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build the routed direct-response and ArchHypo workflows.

    SystemOne is required and exclusively owns request classification; routing
    errors stop execution. Direct and final responses use separate prompts.
    A checkpointer may be injected by the application; it is required to resume
    human review. Graph construction owns no storage.
    """

    response_agent = build_response_generation_agent(
        model,
        tools=tools,
    )
    workflow = StateGraph(AgentState, context_schema=AgentRunContext)
    workflow.add_node("documentary_research", create_documentary_research_node(model))
    workflow.add_node(
        "request_routing",
        create_request_routing_node(system_one_client),
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
        "context_sufficiency_assessment", create_context_sufficiency_node(model)
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
        "artifact_persistence",
        create_artifact_persistence_node(
            artifact_repository,
            chat_model=chat_model_id,
            system_one_model=system_one_model_id,
        ),
    )
    workflow.add_node(
        "response_generation",
        create_response_generation_node(response_agent),
    )
    workflow.add_conditional_edges(
        START, route_entry, ["request_routing", "documentary_research"]
    )
    workflow.add_edge("documentary_research", END)
    workflow.add_conditional_edges(
        "request_routing",
        route_request,
        {
            "architectural_uncertainty_discovery": (
                "architectural_uncertainty_discovery"
            ),
            "hypothesis_formulation": "hypothesis_formulation",
            "context_sufficiency_assessment": "context_sufficiency_assessment",
            "direct_response_generation": "direct_response_generation",
        },
    )
    workflow.add_edge("direct_response_generation", END)
    workflow.add_conditional_edges(
        "architectural_uncertainty_discovery",
        route_after_discovery,
        ["context_sufficiency_assessment", "hypothesis_formulation"],
    )
    workflow.add_conditional_edges(
        "context_sufficiency_assessment",
        route_after_sufficiency,
        {"__end__": END, "hypothesis_formulation": "hypothesis_formulation"},
    )
    workflow.add_conditional_edges(
        "hypothesis_formulation",
        route_after_hypothesis_formulation,
        {
            "hypothesis_review": "hypothesis_review",
            "direct_response_generation": "direct_response_generation",
        },
    )
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
            "artifact_persistence": "artifact_persistence",
            "technical_plan_generation": "technical_plan_generation",
        },
    )
    workflow.add_edge("artifact_persistence", "response_generation")
    workflow.add_edge("response_generation", END)
    return workflow.compile(checkpointer=checkpointer)


__all__ = ["build_graph"]
