"""Node that formulates one hypothesis from the selected uncertainty."""

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_hypothesis_formulation_agent
from archhypo_flow_agent.agents.hypothesis_formulation import SYSTEM_PROMPT
from archhypo_flow_agent.core import AgentRunContext, AgentState

from .support import contextual_system_prompt, latest_user_input


def create_hypothesis_formulation_node(model: BaseChatModel):
    agent = build_hypothesis_formulation_agent(model)

    def formulate(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        uncertainty = state.get("uncertainty")
        discovery = state.get("discovery")
        feedback = state.get("hypothesis_feedback")
        routing = state.get("routing")
        intent = routing.intent if routing is not None else "new_uncertainty"
        if uncertainty is None or discovery is None:
            raise ValueError(
                "discovery and uncertainty are required before formulation"
            )

        material = (
            f"Selected architectural uncertainty:\n{uncertainty}\n\n"
            "Discovery result:\n"
            f"{discovery.model_dump_json(indent=2)}\n\n"
            "Latest user request:\n"
            f"{latest_user_input(state['messages'])}"
        )
        previous = state.get("hypothesis")
        if intent == "alternative_hypothesis":
            previous_results = state.get("result_history", [])
            known_hypotheses = [
                result.hypothesis.model_dump(mode="json")
                for result in previous_results[-5:]
            ]
            if previous is not None:
                previous_payload = previous.model_dump(mode="json")
                if not known_hypotheses or known_hypotheses[-1] != previous_payload:
                    known_hypotheses.append(previous_payload)
            material += (
                "\n\nPreviously proposed hypotheses for this uncertainty "
                "(propose a meaningfully different alternative; do not replace "
                "or repeat them):\n"
                f"{known_hypotheses}"
            )
        elif intent == "revise_hypothesis" and previous is not None:
            material += (
                "\n\nHypothesis to revise, keeping its uncertainty and "
                "addressing the latest request:\n"
                f"{previous.model_dump_json(indent=2)}"
            )
        if feedback:
            material += (
                "\n\nPrevious hypothesis:\n"
                f"{previous.model_dump_json(indent=2) if previous else 'Unavailable'}"
                "\n\nReviewer feedback (address this directly):\n"
                f"{feedback}"
            )

        hypothesis = agent.invoke(
            {
                "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
                "material": material,
            }
        )
        return {
            "hypothesis": hypothesis,
            "uncertainty": hypothesis.uncertainty,
            "hypothesis_feedback": None,
            "hypothesis_review": None,
        }

    return formulate


__all__ = ["create_hypothesis_formulation_node"]
