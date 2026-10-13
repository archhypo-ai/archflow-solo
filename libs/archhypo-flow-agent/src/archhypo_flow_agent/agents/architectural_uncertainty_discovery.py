"""Structured agent for identifying an uncertainty from conversation input."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from archhypo_flow_agent.core import ArchitecturalUncertaintyDiscovery

SYSTEM_PROMPT = """\
You are the ArchHypo Flow architectural uncertainty discovery stage.

Analyze the latest user message and relevant conversation context. Identify one
central uncertainty about a software-architecture decision that can be passed
to hypothesis formulation.

Rules:
- Do not inspect or claim to inspect source files, repositories, or documents.
- Use only facts explicitly provided in the conversation and runtime context.
- Do not invent system properties, requirements, constraints, metrics, or
  evidence.
- If the user stated an uncertainty, normalize it without changing its meaning.
- If the input describes a concern but omits what is unknown, describe the
  missing architectural question; do not assume its answer.
- If no useful architectural uncertainty can be extracted, use
  `insufficient_context`, set `uncertainty` to null, and list the most
  important missing information. The workflow will still continue with an
  explicitly exploratory result.
- Return only one central uncertainty, in the user's language.
"""


def build_architectural_uncertainty_discovery_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | model.with_structured_output(ArchitecturalUncertaintyDiscovery)


__all__ = ["SYSTEM_PROMPT", "build_architectural_uncertainty_discovery_agent"]
