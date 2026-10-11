"""Construction of the conversational ReAct agent."""

from collections.abc import Sequence

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from archhypo_flow_agent.tools import TAVILY_RESEARCH_PROMPT_SNIPPET

_SYSTEM_PROMPT = """\
You are the ArchHypo Flow conversational assistant.
Answer the user's request clearly and honestly. Do not invent facts.
"""


def build_response_generation_agent(
    model: BaseChatModel,
    *,
    tools: Sequence[BaseTool] = (),
):
    """Build a ReAct agent with injected tools and instructions.

    Tool injection is the extension point for dynamically loaded skills. The
    default is intentionally tool-free until the skill subsystem is added.
    """

    selected_tools = list(tools)
    system_prompt = _SYSTEM_PROMPT
    if any(tool.name == "tavily_search" for tool in selected_tools):
        system_prompt = f"{_SYSTEM_PROMPT}\n\n{TAVILY_RESEARCH_PROMPT_SNIPPET}"

    return create_agent(
        model=model,
        tools=selected_tools,
        system_prompt=system_prompt,
    )


__all__ = ["build_response_generation_agent"]
