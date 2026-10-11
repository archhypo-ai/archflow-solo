"""Hypothesis assessment agent."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from archwise_agent.core import HypothesisClassification

SYSTEM_PROMPT = """\
You are the ArchWise Hypothesis Assessor Agent.

Classify exactly one architectural hypothesis. Select exactly one non-functional
requirement and assess both its impact and uncertainty. Every assessment must
include its own explicit justification.

Requirements:
- Select exactly one NFR from: Performance, Security, Reliability, Flexibility,
  Usability, Productivity.
- Select one impact level and one uncertainty level from: Very Low, Low,
  Medium, High, Very High.
- Keep impact and uncertainty as separate assessments.
- Justify the NFR, impact, and uncertainty independently.
- Base every assessment only on the supplied uncertainty and hypothesis.
- Do not classify unrelated concerns from the source material.
- Do not propose technical plans or architectural patterns.
- Use the same language as the input.
"""


def build_hypothesis_assessor_agent(model: BaseChatModel):
    """Build the assessor with a fixed Pydantic response."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | model.with_structured_output(HypothesisClassification)


def make_hypothesis_assessment_input(
    uncertainty: str,
    hypothesis: str,
) -> dict[str, list[HumanMessage]]:
    """Create the typed human-message input for the assessor chain."""

    return {
        "messages": [
            HumanMessage(
                content=(
                    "Architectural uncertainty:\n"
                    f"{uncertainty}\n\n"
                    "Hypothesis:\n"
                    f"{hypothesis}"
                )
            )
        ]
    }


__all__ = [
    "build_hypothesis_assessor_agent",
    "make_hypothesis_assessment_input",
]
