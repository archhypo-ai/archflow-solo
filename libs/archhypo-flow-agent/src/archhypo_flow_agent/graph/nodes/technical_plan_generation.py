"""Node that creates a short technical plan and the aggregate result."""

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import (
    build_catalog_pattern_selection_agent,
    build_technical_plan_generation_agent,
)
from archhypo_flow_agent.agents.technical_plan_generation import (
    CATALOG_SELECTION_PROMPT,
    SYSTEM_PROMPT,
)
from archhypo_flow_agent.core import AgentRunContext, AgentState, ArchHypoResult
from archhypo_flow_agent.tools import CatalogReader, render_references

from .support import contextual_system_prompt


def create_technical_plan_generation_node(model: BaseChatModel):
    selector = build_catalog_pattern_selection_agent(model)
    planner = build_technical_plan_generation_agent(model)
    catalog = CatalogReader()

    def plan(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        discovery = state.get("discovery")
        hypothesis = state.get("hypothesis")
        assessment = state.get("assessment")
        uncertainty = state.get("uncertainty")
        review_feedback = state.get("technical_plan_feedback")
        if (
            discovery is None
            or hypothesis is None
            or assessment is None
            or uncertainty is None
        ):
            raise ValueError(
                "discovery, hypothesis, and assessment are required to plan"
            )

        material = (
            f"Architectural uncertainty:\n{uncertainty}\n\n"
            "Hypothesis:\n"
            f"{hypothesis.model_dump_json(indent=2)}\n\n"
            "Assessment:\n"
            f"{assessment.model_dump_json(indent=2)}"
        )
        if review_feedback:
            material += (
                "\n\nHuman review feedback (address this directly):\n"
                f"{review_feedback}"
            )
        selection = selector.invoke(
            {
                "system_prompt": contextual_system_prompt(
                    CATALOG_SELECTION_PROMPT,
                    runtime,
                ),
                "material": material,
                "catalog_index": catalog.skill_index(),
            }
        )
        references = catalog.read(selection.selected_patterns)
        technical_plan = planner.invoke(
            {
                "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
                "material": (
                    f"{material}\n\n"
                    "Catalog candidate patterns:\n"
                    f"{', '.join(selection.candidate_patterns)}\n\n"
                    "Catalog selection rationale:\n"
                    f"{selection.rationale}\n\n"
                    "Selected official pattern references:\n"
                    f"{render_references(references)}"
                ),
            }
        )
        unauthorized_patterns = {
            item.pattern
            for item in technical_plan.items
            if item.pattern not in selection.selected_patterns
        }
        if unauthorized_patterns:
            raise ValueError(
                "The technical plan used patterns without reading their catalog "
                "references: "
                + ", ".join(sorted(unauthorized_patterns))
            )
        result = ArchHypoResult(
            uncertainty=uncertainty,
            discovery=discovery,
            hypothesis=hypothesis,
            assessment=assessment,
            technical_plan=technical_plan,
        )
        return {
            "technical_plan": technical_plan,
            "technical_plan_review": None,
            "technical_plan_feedback": None,
            "result": result,
        }

    return plan


__all__ = ["create_technical_plan_generation_node"]
