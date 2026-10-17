"""Formulate, revise, or propose a distinct hypothesis for one uncertainty."""

import json
import unicodedata
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langgraph.runtime import Runtime

from archhypo_flow_agent.agents import build_hypothesis_formulation_agent
from archhypo_flow_agent.agents.hypothesis_formulation import (
    NOVELTY_PROMPT,
    OPERATION_INSTRUCTIONS,
    SYSTEM_PROMPT,
    build_hypothesis_novelty_agent,
)
from archhypo_flow_agent.core import AgentRunContext, AgentState, Hypothesis

from .support import contextual_system_prompt, latest_user_input


def create_hypothesis_formulation_node(model: BaseChatModel):
    agent = build_hypothesis_formulation_agent(model)
    novelty_agent = build_hypothesis_novelty_agent(model)

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
        known_hypotheses = _previous_hypotheses(state, include_current=not feedback)
        if intent == "alternative_hypothesis":
            material += (
                "\n\nPreviously proposed hypotheses for this uncertainty "
                "(propose a meaningfully different alternative; do not replace "
                "or repeat them):\n"
                + json.dumps(
                    [item.model_dump(mode="json") for item in known_hypotheses],
                    ensure_ascii=False,
                )
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

        operation = (
            "revise_hypothesis"
            if feedback or intent == "revise_hypothesis"
            else "alternative_hypothesis"
            if intent == "alternative_hypothesis"
            else "new_uncertainty"
        )
        system_prompt = contextual_system_prompt(
            f"{SYSTEM_PROMPT}\n\n{OPERATION_INSTRUCTIONS[operation]}", runtime
        )
        attempts = 2 if intent == "alternative_hypothesis" else 1
        retry_material = material
        for _ in range(attempts):
            proposal = agent.invoke(
                {"system_prompt": system_prompt, "material": retry_material}
            )
            if proposal.clarification_question is not None:
                return {"formulation_question": proposal.clarification_question}

            hypothesis = proposal.hypothesis
            if hypothesis is None:
                raise ValueError("formulation returned neither hypothesis nor question")
            rejection = None
            if intent == "alternative_hypothesis" and known_hypotheses:
                rejection = _duplicate_reason(hypothesis, known_hypotheses)
                if rejection is None:
                    novelty = novelty_agent.invoke(
                        {
                            "system_prompt": contextual_system_prompt(
                                NOVELTY_PROMPT, runtime
                            ),
                            "material": json.dumps(
                                {
                                    "uncertainty": uncertainty,
                                    "candidate": hypothesis.model_dump(mode="json"),
                                    "previous_hypotheses": [
                                        item.model_dump(mode="json")
                                        for item in known_hypotheses
                                    ],
                                },
                                ensure_ascii=False,
                            ),
                        }
                    )
                    if not novelty.is_distinct:
                        rejection = novelty.rationale
            if rejection is not None:
                retry_material = (
                    f"{material}\n\nRejected alternative candidate:\n"
                    f"{hypothesis.model_dump_json(indent=2)}\n\n"
                    f"Validation feedback: {rejection}\n"
                    "Return a genuinely different claim with a distinct title, "
                    "or ask a clarification question. Do not invent new facts."
                )
                continue

            if intent in {"alternative_hypothesis", "revise_hypothesis"} or feedback:
                hypothesis = hypothesis.model_copy(update={"uncertainty": uncertainty})
            return {
                "hypothesis": hypothesis,
                "uncertainty": hypothesis.uncertainty,
                "formulation_question": None,
                "hypothesis_feedback": None,
                "hypothesis_review": None,
                "assessment": None,
                "technical_plan": None,
                "technical_plan_review": None,
                "technical_plan_feedback": None,
                "result": None,
            }

        context = runtime.context if runtime is not None else None
        language = context.get("language", "en") if isinstance(context, dict) else "en"
        question = (
            "Não consegui formular uma hipótese realmente diferente com as "
            "informações disponíveis. Qual outra premissa ou alternativa "
            "arquitetural devemos investigar para essa mesma incerteza?"
            if language == "pt-BR"
            else "I couldn't formulate a genuinely different hypothesis from "
            "the available information. Which other assumption or architectural "
            "alternative should we investigate for this same uncertainty?"
        )
        return {"formulation_question": question}

    return formulate


def route_after_hypothesis_formulation(
    state: AgentState,
) -> Literal["hypothesis_review", "direct_response_generation"]:
    if state.get("formulation_question"):
        return "direct_response_generation"
    if state.get("hypothesis") is None:
        raise ValueError("a hypothesis or clarification question is required")
    return "hypothesis_review"


def _previous_hypotheses(
    state: AgentState, *, include_current: bool
) -> list[Hypothesis]:
    """Select only hypotheses from the active uncertainty, without duplicates."""

    discovery = state.get("discovery")
    hypotheses = [
        result.hypothesis
        for result in state.get("result_history", [])
        if result.discovery == discovery
    ]
    if include_current and (current := state.get("hypothesis")) is not None:
        hypotheses.append(current)
    unique = {
        (_normalized(item.statement), _normalized(item.title)): item
        for item in hypotheses
    }
    return list(unique.values())


def _duplicate_reason(candidate: Hypothesis, previous: list[Hypothesis]) -> str | None:
    if any(
        _normalized(candidate.statement) == _normalized(item.statement)
        for item in previous
    ):
        return "The testable statement repeats a previously proposed hypothesis."
    if any(
        _normalized(candidate.title) == _normalized(item.title) for item in previous
    ):
        return "The title repeats an existing card; use a distinct descriptive title."
    return None


def _normalized(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split()).rstrip(".!?")


__all__ = ["create_hypothesis_formulation_node", "route_after_hypothesis_formulation"]
