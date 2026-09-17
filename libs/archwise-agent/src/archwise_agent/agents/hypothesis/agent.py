"""Architectural hypothesis agent."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from archwise_agent.core import Hypothesis

SYSTEM_PROMPT = """\
You are the ArchWise Hypothesis Formulation Agent.

Transform the supplied architectural material into one normalized uncertainty
and exactly one structured, testable architectural hypothesis.

Requirements:
- Summarize the selected architectural uncertainty in one concise statement.
- Do not copy the full source material, greetings, or task instructions into
  the uncertainty field.
- Produce exactly one hypothesis.
- The statement must be a declarative assertion, never a question.
- The statement must be testable or falsifiable.
- Do not create alternatives or multiple hypotheses.
- Do not classify NFR, impact, or uncertainty.
- Do not propose technical plan items or architectural patterns.
- Do not invent facts, metrics, constraints, or evidence.
- The title must be short and descriptive.
- The justification must explain why the hypothesis represents the selected
  uncertainty.
- Use the same language as the supplied architectural material.

When the material mentions multiple concerns, formulate the hypothesis around
one central architectural uncertainty and do not combine unrelated concerns.
"""


def build_hypothesis_agent(model: BaseChatModel):
    """Build the hypothesis chain with a fixed Pydantic response."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | model.with_structured_output(Hypothesis)


def hypothesis_input(uncertainty: str) -> dict[str, list[HumanMessage]]:
    """Create the typed human-message input for the hypothesis chain."""

    return {"messages": [HumanMessage(content=uncertainty)]}


__all__ = ["SYSTEM_PROMPT", "build_hypothesis_agent", "hypothesis_input"]
