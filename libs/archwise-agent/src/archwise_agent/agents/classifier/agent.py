"""Hypothesis classification agent."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from archwise_agent.core import HypothesisClassification

SYSTEM_PROMPT = """\
You are the ArchWise Hypothesis Classification Agent.

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
- Do not propose technical plans or architectural patterns.
- Use the same language as the input.
"""


def build_classifier_agent(model: BaseChatModel):
    """Build the classifier with a fixed Pydantic response."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "Architectural uncertainty:\n{uncertainty}\n\n"
                "Hypothesis:\n{hypothesis}",
            ),
        ]
    )
    return prompt | model.with_structured_output(HypothesisClassification)


__all__ = ["build_classifier_agent"]
