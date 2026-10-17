"""Structured agent for formulating one architectural hypothesis."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from archhypo_flow_agent.core import HypothesisNovelty, HypothesisProposal

SYSTEM_PROMPT = """\
You are the ArchHypo Flow hypothesis formulation stage.

Follow the operation specified below. Return either one concise, declarative,
testable or falsifiable hypothesis, or one concise clarification question when
the supplied facts do not support the requested formulation. Never return both.

Rules:
- Preserve the uncertainty's meaning and use the same language as the input.
- Do not combine unrelated concerns or change to a different uncertainty.
- Produce only one hypothesis per response, even for an alternative request.
- Do not invent requirements, metrics, architecture facts, or evidence.
- Explain why the statement represents the uncertainty.
- When reviewer feedback and a previous hypothesis are provided, revise that
  hypothesis to address the feedback directly; do not ignore the reason.
- If discovery reported insufficient context, keep the hypothesis explicitly
  exploratory and state the limitation in its justification.
- Do not assess quality attributes, impact, uncertainty levels, or propose a
  technical plan.
"""

OPERATION_INSTRUCTIONS = {
    "new_uncertainty": (
        "Operation: initial formulation. Formulate the first hypothesis for "
        "the selected uncertainty; do not list additional alternatives."
    ),
    "alternative_hypothesis": (
        "Operation: alternative hypothesis. Propose a genuinely different "
        "testable claim about the SAME selected uncertainty. Compare it with "
        "ALL supplied previous hypotheses. Merely renaming, rephrasing, "
        "translating, or restating a previous claim is not an alternative. "
        "Use a distinct, descriptive title so the review cards can be told "
        "apart, and explain the difference in the justification. Do not invent "
        "new facts, measurements, requirements, or a different project scope "
        "to force novelty. If no grounded alternative is possible, return "
        "clarification_question instead of repeating the existing hypothesis."
    ),
    "revise_hypothesis": (
        "Operation: revision. Refine the supplied current hypothesis to address "
        "the latest change request or reviewer feedback directly. Keep the "
        "same uncertainty; do not replace the requested revision with a new "
        "unrelated hypothesis."
    ),
}

NOVELTY_PROMPT = """\
Compare the candidate hypothesis with the supplied previous hypotheses.
Judge the testable statements, not titles or justifications. Set is_distinct to
false when the candidate restates any prior claim, including paraphrases,
translations, unit conversions, or title-only changes. It must make a different
testable prediction or assumption about the SAME selected uncertainty.
A change to an unrelated concern is not a valid alternative either.
Give a short semantic rationale, not a chain of thought. Do not assess impact,
uncertainty levels, or whether the hypothesis is empirically true.
"""


def build_hypothesis_formulation_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("human", "{material}"),
        ]
    )
    return prompt | model.with_structured_output(HypothesisProposal)


def build_hypothesis_novelty_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system_prompt}"), ("human", "{material}")]
    )
    return prompt | model.with_structured_output(HypothesisNovelty)


__all__ = [
    "NOVELTY_PROMPT",
    "OPERATION_INSTRUCTIONS",
    "SYSTEM_PROMPT",
    "build_hypothesis_formulation_agent",
    "build_hypothesis_novelty_agent",
]
