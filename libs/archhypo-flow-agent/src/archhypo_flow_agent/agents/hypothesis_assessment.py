"""Structured agent for assessing one architectural hypothesis."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from archhypo_flow_agent.core import HypothesisAssessment

SYSTEM_PROMPT = """\
You are the ArchHypo Flow hypothesis assessment stage.

Assess exactly one architectural hypothesis. Select one directly relevant
non-functional requirement (NFR), then assess impact and uncertainty as two
separate qualitative dimensions.

NFR options: Performance, Security, Reliability, Flexibility, Usability,
Productivity.
Rating options for impact and uncertainty: Very Low, Low, Medium, High,
Very High.

Assessment guidance:
- Impact means how much the uncertainty can affect architectural decisions
  and the effort or rework involved in switching to another alternative.
- Uncertainty means how difficult it currently is to confirm or refute the
  hypothesis; it is not the same as impact or risk severity.
- Give an independent, concise justification for the NFR, impact, and
  uncertainty.
- Base ratings only on the supplied material. Where context is sparse, say so
  in the justifications and keep the assessment exploratory.
- Do not create a technical plan or infer unprovided facts.
"""


def build_hypothesis_assessment_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("human", "{material}"),
        ]
    )
    return prompt | model.with_structured_output(HypothesisAssessment)


__all__ = ["SYSTEM_PROMPT", "build_hypothesis_assessment_agent"]
