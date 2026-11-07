"""Assess whether an architectural question has enough context to proceed."""

from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.runtime import Runtime
from pydantic import BaseModel, ConfigDict, Field, model_validator

from archhypo_flow_agent.core import AgentRunContext, AgentState

from .support import contextual_system_prompt

PROMPT = """\
Assess whether the conversation provides enough context to formulate one useful,
testable architectural hypothesis. Use only the conversation and supplied
context; do not invent facts or claim to inspect documents. A decision or
concern and its relevant scenario must be understandable, but do not demand
metrics, a solution, or certainty about the outcome. Unknowns can be explored
by a hypothesis. Do not ask again for information already supplied; accept 'I
don't know' and acknowledge limits. If an essential detail is missing, ask one
concise, prioritized question in the user's language. Otherwise provide a
normalized central uncertainty. Do not formulate a hypothesis or plan.
"""


class ContextSufficiency(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["sufficient", "needs_clarification"]
    uncertainty: str | None = Field(default=None, min_length=1)
    missing_information: list[str] = Field(default_factory=list, max_length=5)
    question: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_result(self):
        if self.status == "sufficient" and not (self.uncertainty or "").strip():
            raise ValueError("sufficient context requires an uncertainty")
        if self.status == "needs_clarification" and not (self.question or "").strip():
            raise ValueError("insufficient context requires a question")
        return self


def create_context_sufficiency_node(model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system_prompt}"), MessagesPlaceholder("messages")]
    )
    agent = prompt | model.with_structured_output(ContextSufficiency)

    def assess(state: AgentState, runtime: Runtime[AgentRunContext] | None = None):
        report = agent.invoke(
            {
                "system_prompt": contextual_system_prompt(PROMPT, runtime),
                "messages": state["messages"],
            }
        )
        update: dict[str, object] = {
            "context_sufficiency": report.model_dump(mode="json"),
            "interview_pending": report.status == "needs_clarification",
        }
        if report.status == "needs_clarification":
            update["messages"] = [AIMessage(content=report.question)]
        else:
            update["uncertainty"] = report.uncertainty
            discovery = state.get("discovery")
            if discovery is not None:
                update["discovery"] = discovery.model_copy(
                    update={
                        "status": "identified",
                        "uncertainty": report.uncertainty,
                        "missing_information": report.missing_information,
                    }
                )
        return update

    return assess


def route_after_discovery(state: AgentState) -> str:
    if state.get("hitl_enabled", True):
        return "context_sufficiency_assessment"
    return "hypothesis_formulation"


def route_after_sufficiency(state: AgentState) -> str:
    return "__end__" if state.get("interview_pending") else "hypothesis_formulation"
