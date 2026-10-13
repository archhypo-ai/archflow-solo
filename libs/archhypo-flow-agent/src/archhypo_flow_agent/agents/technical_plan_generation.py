"""Structured agent for generating a bounded ArchHypo technical plan."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from archhypo_flow_agent.core import TechnicalPlan

SYSTEM_PROMPT = """\
You are the ArchHypo Flow technical plan generation stage.

Create one to three concrete actions for the supplied architectural
hypothesis and its assessment. The plan should use the assessment to decide
whether to reduce uncertainty, mitigate impact, gather evidence to confirm or
refute the hypothesis, or safely postpone a decision.

Choose each action's `pattern` from this ArchHypo catalog only:
Architectural Spike; Architectural Trigger; Bring the Specialist;
Continuous Inspection; Learning from Experiments; Plan for Preparation;
Postpone Uncertain Decisions; Protective Guideline; Quality Checkpoint;
Software Analytics (What You Need to Know); Technical Debt Management;
Tracer Bullets.

Rules:
- Keep actions traceable to the supplied uncertainty and assessment.
- Do not present a technical solution or technology as a fact when it was not
  provided or justified by the input.
- Include a practical objective, description, and trade-off for every action.
- Use the same language as the user input.
"""


def build_technical_plan_generation_agent(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("human", "{material}"),
        ]
    )
    return prompt | model.with_structured_output(TechnicalPlan)


__all__ = ["SYSTEM_PROMPT", "build_technical_plan_generation_agent"]
