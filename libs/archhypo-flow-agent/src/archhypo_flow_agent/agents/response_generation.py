"""Construction of the conversational ReAct agent."""

from collections.abc import Sequence

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

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

    return create_agent(
        model=model,
        tools=list(tools),
        system_prompt=_SYSTEM_PROMPT,
    )


__all__ = ["build_response_generation_agent"]
