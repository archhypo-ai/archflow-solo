"""Node that assesses NFR, impact, and uncertainty for one hypothesis."""

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime
from pydantic import ValidationError

from archhypo_flow_agent.agents import build_hypothesis_assessment_agent
from archhypo_flow_agent.agents.hypothesis_assessment import SYSTEM_PROMPT
from archhypo_flow_agent.core import (
    AgentRunContext,
    AgentState,
    StructuredOutputError,
)

from .support import contextual_system_prompt


def create_hypothesis_assessment_node(model: BaseChatModel):
    agent = build_hypothesis_assessment_agent(model)

    def assess(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        hypothesis = state.get("hypothesis")
        uncertainty = state.get("uncertainty")
        if hypothesis is None or uncertainty is None:
            raise ValueError(
                "hypothesis and uncertainty are required before assessment"
            )

        agent_input = {
            "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
            "material": (
                f"Architectural uncertainty:\n{uncertainty}\n\n"
                "Hypothesis:\n"
                f"{hypothesis.model_dump_json(indent=2)}"
            ),
            "repair_feedback": "",
        }
        try:
            assessment = agent.invoke(agent_input)
        except ValidationError as first_error:
            retry_input = {
                **agent_input,
                "repair_feedback": _repair_guidance(first_error),
            }
            try:
                assessment = agent.invoke(retry_input)
            except ValidationError as second_error:
                raise StructuredOutputError(
                    stage="hypothesis_assessment",
                    attempts=2,
                ) from second_error
        return {"assessment": assessment}

    return assess


def _repair_guidance(error: ValidationError) -> str:
    missing_fields = sorted(
        {
            ".".join(str(part) for part in item["loc"])
            for item in error.errors()
            if item["type"] == "missing"
        }
    )
    if missing_fields:
        details = "\n".join(
            f"- Required field missing: {field}" for field in missing_fields
        )
    else:
        details = (
            "- The output did not satisfy the required HypothesisAssessment schema."
        )
    return (
        "Your previous output failed structured validation. Regenerate the full "
        "assessment, preserving valid ratings and including every required "
        "justification. Do not return a partial object.\n"
        f"Validation feedback:\n{details}"
    )


__all__ = ["create_hypothesis_assessment_node"]
