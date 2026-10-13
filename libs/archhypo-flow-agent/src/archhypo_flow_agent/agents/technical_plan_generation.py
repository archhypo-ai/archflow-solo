"""Structured agent for generating a bounded ArchHypo technical plan."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from archhypo_flow_agent.core import CatalogPatternSelection, TechnicalPlan

CATALOG_SELECTION_PROMPT = """\
You are the ArchHypo catalog pattern selector.

Screen the complete catalog skill index against the supplied uncertainty,
hypothesis, and assessment. Treat each pattern's "Use when" summary as the
primary selection signal, and consider its listed related official patterns as
additional candidates only when relevant.

Rules:
- Screen the whole catalog, not just the first matching rows.
- Return at most five distinct candidate patterns in total.
- Select one to three strongest patterns from those candidates for full
  reference reading; selected patterns must be members of the candidate list.
- Prefer direct matches to the uncertainty. A related pattern is not relevant
  merely because it appears in the index.
- Do not invent patterns or facts about the project.
- Keep the rationale concise and specific to the supplied hypothesis.
"""

SYSTEM_PROMPT = """\
You are the ArchHypo Flow technical plan generation stage.

Create one to three concrete actions for the supplied architectural
hypothesis and its assessment, grounded in the selected official pattern
references provided in the input. Use the assessment to decide whether to
reduce uncertainty, mitigate impact, gather evidence to confirm or refute the
hypothesis, or safely postpone a decision.

Rules:
- Keep actions traceable to the supplied uncertainty and assessment.
- Use only patterns selected for reference reading; do not introduce another
  pattern based only on its name or a related-pattern link.
- Do not present a technical solution or technology as a fact when it was not
  provided or justified by the input.
- Include a practical objective, description, and trade-off for every action.
- When human review feedback is provided, address it directly in the revised
  plan and keep unaffected parts that remain valid.
- Use the same language as the user input.
"""


def build_catalog_pattern_selection_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("human", "{material}\n\nCatalog skill index:\n{catalog_index}"),
        ]
    )
    return prompt | model.with_structured_output(CatalogPatternSelection)


def build_technical_plan_generation_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("human", "{material}"),
        ]
    )
    return prompt | model.with_structured_output(TechnicalPlan)


__all__ = [
    "CATALOG_SELECTION_PROMPT",
    "SYSTEM_PROMPT",
    "build_catalog_pattern_selection_agent",
    "build_technical_plan_generation_agent",
]
