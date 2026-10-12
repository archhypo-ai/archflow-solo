"""Construction of the conversational ReAct agent."""

from collections.abc import Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from archhypo_flow_agent.core import AgentRunContext
from archhypo_flow_agent.tools import TAVILY_RESEARCH_PROMPT_SNIPPET

from .prompts import build_system_prompt

_SYSTEM_PROMPT = """\
You are the ArchHypo Flow conversational assistant.
Answer the user's request clearly and honestly. Do not invent facts.
"""


def build_response_generation_agent(
    model: BaseChatModel,
    *,
    tools: Sequence[BaseTool] = (),
):
    """Build a ReAct agent with context composed into each model system prompt."""

    selected_tools = list(tools)
    base_system_prompt = _SYSTEM_PROMPT
    if any(tool.name == "tavily_search" for tool in selected_tools):
        base_system_prompt = f"{_SYSTEM_PROMPT}\n\n{TAVILY_RESEARCH_PROMPT_SNIPPET}"

    @dynamic_prompt
    def prompt_for_execution(request: ModelRequest) -> str:
        context = request.runtime.context if request.runtime is not None else None
        if not isinstance(context, dict):
            context = {}
        return build_system_prompt(
            base_system_prompt,
            global_context=str(context.get("global_context", "")),
            project_context=str(context.get("project_context", "")),
        )

    return create_agent(
        model=model,
        tools=selected_tools,
        system_prompt=base_system_prompt,
        middleware=[prompt_for_execution],
        context_schema=AgentRunContext,
    )


__all__ = ["build_response_generation_agent"]
