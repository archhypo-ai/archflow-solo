"""Route request intent to either the ArchHypo path or a direct response."""

from __future__ import annotations

import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langgraph.runtime import Runtime
from pydantic import ValidationError

from archhypo_flow_agent.agents import build_request_routing_agent
from archhypo_flow_agent.agents.request_routing import (
    REQUEST_INTENT_CRITERIA,
    SYSTEM_ONE_ROUTING_QUESTION,
    SYSTEM_PROMPT,
)
from archhypo_flow_agent.core import (
    AgentRunContext,
    AgentState,
    RequestRoute,
    RequestRouting,
)
from archhypo_flow_agent.providers import (
    SystemOneClient,
    SystemOneError,
    SystemOneResponseError,
)

from .support import analysis_context, contextual_system_prompt, latest_user_input

logger = logging.getLogger(__name__)

def create_request_routing_node(
    model: BaseChatModel,
    *,
    system_one_client: SystemOneClient | None = None,
):
    """Use SystemOne for routing and the main model as a resilient fallback."""

    fallback_router = build_request_routing_agent(model)

    def route(
        state: AgentState,
        runtime: Runtime[AgentRunContext] | None = None,
    ) -> dict[str, object]:
        latest_message = latest_user_input(state["messages"])
        current_analysis = analysis_context(state)
        fallback_input = {
            "messages": state["messages"],
            "system_prompt": contextual_system_prompt(SYSTEM_PROMPT, runtime),
            "analysis_context": json.dumps(
                current_analysis,
                ensure_ascii=False,
                default=str,
            ),
        }

        if system_one_client is None:
            routing = RequestRouting.model_validate(
                fallback_router.invoke(fallback_input)
            )
        else:
            try:
                decision = system_one_client.decide(
                    state=_system_one_state(
                        state,
                        runtime,
                        latest_message,
                        current_analysis,
                    ),
                    questions={"intent": SYSTEM_ONE_ROUTING_QUESTION},
                )
                answer = decision.answers.get("intent")
                if answer is None or answer.choice not in REQUEST_INTENT_CRITERIA:
                    raise SystemOneResponseError(
                        "SystemOne returned an unknown request intent"
                    )
                try:
                    routing = RequestRouting.model_validate(
                        {"intent": answer.choice}
                    )
                except ValidationError as error:
                    raise SystemOneResponseError(
                        "SystemOne returned an invalid request intent"
                    ) from error
            except SystemOneError as error:
                logger.warning(
                    "SystemOne routing failed; using the structured LLM fallback: %s",
                    type(error).__name__,
                )
                routing = RequestRouting.model_validate(
                    fallback_router.invoke(fallback_input)
                )

        return _prepare_route(state, routing)

    return route


def route_request(state: AgentState) -> RequestRoute:
    """Return the next node selected by the validated routing contract."""

    routing = state.get("routing")
    if routing is None:
        raise ValueError("request routing is required")
    return routing.route


def _prepare_route(
    state: AgentState,
    routing: RequestRouting,
) -> dict[str, object]:
    if routing.route == "direct_response_generation":
        # Direct questions must retain the active and previous results so the
        # response stage can answer against them without mutating the workflow.
        return {"routing": routing}

    if routing.intent in {"alternative_hypothesis", "revise_hypothesis"} and (
        state.get("hypothesis") is None
        or state.get("discovery") is None
        or state.get("uncertainty") is None
    ):
        # Do not formulate against a guessed or missing target. The direct
        # response stage will ask which uncertainty/hypothesis the user means.
        return {"routing": RequestRouting(intent="clarification")}

    result_history = list(state.get("result_history", []))
    active_result = state.get("result")
    if active_result is not None and active_result not in result_history:
        result_history.append(active_result)

    update: dict[str, object] = {
        "routing": routing,
        "result_history": result_history,
        "hypothesis_review": None,
        "hypothesis_feedback": None,
        "assessment": None,
        "technical_plan": None,
        "technical_plan_review": None,
        "technical_plan_feedback": None,
        "result": None,
    }

    if routing.intent == "new_uncertainty":
        update.update(
            {
                "discovery": None,
                "uncertainty": None,
                "hypothesis": None,
            }
        )
    # For an alternative/revision, keep the active discovery, uncertainty, and
    # hypothesis available to formulation. It will replace only the active
    # hypothesis after the previous completed result has been archived.
    return update


def _system_one_state(
    state: AgentState,
    runtime: Runtime[AgentRunContext] | None,
    latest_message: str,
    current_analysis: dict[str, object],
) -> dict[str, object]:
    context = runtime.context if runtime is not None else None
    if not isinstance(context, dict):
        context = {}
    return {
        "latest_user_message": latest_message,
        "recent_conversation": [
            {
                "role": message.type,
                "content": _message_content(message)[:2_000],
            }
            for message in state["messages"][-12:]
        ],
        "analysis": current_analysis,
        "global_context": str(context.get("global_context", ""))[:4_000],
        "project_context": str(context.get("project_context", ""))[:4_000],
    }


def _message_content(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(block["text"])
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        )
    return str(content)


__all__ = ["create_request_routing_node", "route_request"]
