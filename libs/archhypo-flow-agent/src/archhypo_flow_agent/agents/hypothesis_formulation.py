"""Structured agent for formulating one architectural hypothesis."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from archhypo_flow_agent.core import Hypothesis

SYSTEM_PROMPT = """\
You are the ArchHypo Flow hypothesis formulation stage.

Transform the selected architectural uncertainty into exactly one concise,
declarative, testable or falsifiable hypothesis.

Rules:
- Preserve the uncertainty's meaning and use the same language as the input.
- Do not combine unrelated concerns or create alternatives.
- Do not invent requirements, metrics, architecture facts, or evidence.
- Explain why the statement represents the uncertainty.
- When reviewer feedback and a previous hypothesis are provided, revise that
  hypothesis to address the feedback directly; do not ignore the reason.
- If discovery reported insufficient context, keep the hypothesis explicitly
  exploratory and state the limitation in its justification.
- Do not assess quality attributes, impact, uncertainty levels, or propose a
  technical plan.
"""


def build_hypothesis_formulation_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("human", "{material}"),
        ]
    )
    return prompt | model.with_structured_output(Hypothesis)


__all__ = ["SYSTEM_PROMPT", "build_hypothesis_formulation_agent"]
