"""Linear ArchWise workflow orchestrator."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from archwise_agent.agents.classifier import build_classifier_agent
from archwise_agent.agents.hypothesis import build_hypothesis_agent
from archwise_agent.agents.technical_plan import build_technical_plan_agent
from archwise_agent.config import AgentSettings
from archwise_agent.core import ArchHypoState, RunContext
from archwise_agent.providers import create_openrouter_model

from .nodes import (
    create_classify_hypothesis_node,
    create_formulate_hypothesis_node,
    create_technical_plan_node,
)


def build_archwise_agent(
    *,
    model: BaseChatModel | None = None,
    configuration: AgentSettings | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build the linear ArchHypo workflow."""

    chat_model = model or create_openrouter_model(configuration)
    hypothesis_agent = build_hypothesis_agent(chat_model)
    classifier_agent = build_classifier_agent(chat_model)
    technical_plan_agent = build_technical_plan_agent(chat_model)

    workflow = StateGraph(ArchHypoState, context_schema=RunContext)
    workflow.add_node(
        "formulate_hypothesis",
        create_formulate_hypothesis_node(hypothesis_agent),
    )
    workflow.add_node(
        "classify_hypothesis",
        create_classify_hypothesis_node(classifier_agent),
    )
    workflow.add_node(
        "create_technical_plan",
        create_technical_plan_node(technical_plan_agent),
    )
    workflow.add_edge(START, "formulate_hypothesis")
    workflow.add_edge("formulate_hypothesis", "classify_hypothesis")
    workflow.add_edge("classify_hypothesis", "create_technical_plan")
    workflow.add_edge("create_technical_plan", END)

    return workflow.compile(
        checkpointer=(checkpointer if checkpointer is not None else InMemorySaver())
    )


__all__ = ["build_archwise_agent"]
