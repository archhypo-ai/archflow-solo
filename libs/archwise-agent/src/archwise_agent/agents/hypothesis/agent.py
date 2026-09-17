"""Architectural hypothesis agent."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from archwise_agent.core import Hypothesis

SYSTEM_PROMPT = """\
You are the ArchWise Hypothesis Formulation Agent.

Transform exactly one architectural uncertainty into exactly one structured and
testable architectural hypothesis.

Requirements:
- Produce exactly one hypothesis.
- The statement must be a declarative assertion, never a question.
- The statement must be testable or falsifiable.
- Do not create alternatives or multiple hypotheses.
- Do not classify NFR, impact, or uncertainty.
- Do not propose technical plan items or architectural patterns.
- Do not invent facts, metrics, constraints, or evidence.
- The title must be short and descriptive.
- The justification must explain why the hypothesis is a suitable formulation
  of the supplied uncertainty.
- Use the same language as the input.

Focus only on the supplied uncertainty.
"""


def build_hypothesis_agent(model: BaseChatModel):
    """Build the hypothesis chain with a fixed Pydantic response."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{uncertainty}"),
        ]
    )
    return prompt | model.with_structured_output(Hypothesis)


__all__ = ["build_hypothesis_agent"]
