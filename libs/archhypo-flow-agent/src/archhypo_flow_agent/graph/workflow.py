"""Linear LangGraph workflow for the ArchHypo validation slice."""

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from archhypo_flow_agent.agents import build_response_generation_agent
from archhypo_flow_agent.core import AgentRunContext, AgentState
from archhypo_flow_agent.graph.nodes import (
    create_architectural_uncertainty_discovery_node,
    create_hypothesis_assessment_node,
    create_hypothesis_formulation_node,
    create_response_generation_node,
    create_technical_plan_generation_node,
    request_routing_node,
)


def build_graph(
    model: BaseChatModel,
    *,
    tools: Sequence[BaseTool] = (),
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build the fixed routing, discovery, hypothesis, assessment, and plan flow.

    The final response node reuses the existing LangChain ReAct agent. A
    checkpointer may be injected by the application; graph construction owns
    no storage.
    """

    response_agent = build_response_generation_agent(
        model,
        tools=tools,
    )
    workflow = StateGraph(AgentState, context_schema=AgentRunContext)
    workflow.add_node("request_routing", request_routing_node)
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
    workflow.add_node(
        "technical_plan_generation",
        create_technical_plan_generation_node(model),
    )
    workflow.add_node(
        "response_generation",
        create_response_generation_node(response_agent),
    )
    workflow.add_edge(START, "request_routing")
    workflow.add_edge("request_routing", "architectural_uncertainty_discovery")
    workflow.add_edge("architectural_uncertainty_discovery", "hypothesis_formulation")
    workflow.add_edge("hypothesis_formulation", "hypothesis_assessment")
    workflow.add_edge("hypothesis_assessment", "technical_plan_generation")
    workflow.add_edge("technical_plan_generation", "response_generation")
    workflow.add_edge("response_generation", END)
    return workflow.compile(checkpointer=checkpointer)


__all__ = ["build_graph"]
