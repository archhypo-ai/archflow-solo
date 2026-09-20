"""Architectural hypothesis agent."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from archwise_agent.core import Hypothesis, UncertaintyDiscoveryReport

SYSTEM_PROMPT = """\
You are the ArchWise Hypothesis Formulator Agent.

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


def build_hypothesis_formulator_agent(model: BaseChatModel):
    """Build the hypothesis chain with a fixed Pydantic response."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | model.with_structured_output(Hypothesis)


def make_hypothesis_input(
    uncertainty: str,
    discovery: UncertaintyDiscoveryReport | None = None,
) -> dict[str, list[HumanMessage]]:
    """Create typed input with optional workspace discovery evidence."""

    content = uncertainty
    if discovery is not None:
        content = (
            "User-provided architectural material:\n"
            f"{uncertainty}\n\n"
            "Workspace discovery report:\n"
            f"{discovery.model_dump_json(indent=2)}"
        )
    return {"messages": [HumanMessage(content=content)]}


__all__ = [
    "build_hypothesis_formulator_agent",
    "make_hypothesis_input",
]
