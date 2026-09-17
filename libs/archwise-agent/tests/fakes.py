"""Deterministic test doubles for the ArchWise agents."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr

from archwise_agent.core import (
    ArchHypo,
    Hypothesis,
    HypothesisClassification,
    RequestRouting,
    TechnicalPlan,
    UserResponse,
)


class FakeWorkflowChatModel(FakeListChatModel):
    """Fake model supporting structured output and technical-plan tools."""

    _statements: list[str] = PrivateAttr()
    _uncertainties: list[str] = PrivateAttr()
    _hypothesis_index: int = PrivateAttr(default=0)
    _tool_mode: bool = PrivateAttr(default=False)
    _delay: float = PrivateAttr(default=0.0)
    _route: str = PrivateAttr(default="archwise_workflow")
    _direct_response: str = PrivateAttr(default="")

    def __init__(
        self,
        statements: list[str],
        *,
        uncertainties: list[str] | None = None,
        sleep: float | None = None,
        route: str = "archwise_workflow",
        direct_response: str = "",
    ) -> None:
        super().__init__(
            responses=["unused"],
            disable_streaming=True,
        )
        self._statements = statements
        self._uncertainties = uncertainties or [""] * len(statements)
        self._delay = sleep or 0.0
        self._route = route
        self._direct_response = direct_response

    def with_structured_output(
        self,
        schema: Any,
        **kwargs: Any,
    ):
        return RunnableLambda(lambda value: self._structured_response(schema, value))

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ):
        self._tool_mode = True
        return self

    def _structured_response(self, schema: Any, value: Any) -> Any:
        if self._delay:
            time.sleep(self._delay)

        if schema is RequestRouting:
            return RequestRouting(route=self._route)
        if schema is UserResponse:
            return UserResponse(
                message=(
                    self._direct_response
                    if self._route == "direct_response"
                    else "ArchWise response."
                )
            )
        if schema is Hypothesis:
            index = self._hypothesis_index
            self._hypothesis_index += 1
            uncertainty = self._uncertainties[index]
            if not uncertainty:
                uncertainty = _message_content(value)
            return Hypothesis(
                uncertainty=uncertainty,
                title=f"Hypothesis {index + 1}",
                statement=self._statements[index],
                justification="Derived from the supplied uncertainty.",
            )
        if schema is HypothesisClassification:
            return HypothesisClassification(
                nfr="Performance",
                nfr_justification="The hypothesis concerns system capacity.",
                impact="High",
                impact_justification="Failure affects peak operation.",
                uncertainty="High",
                uncertainty_justification="The projected load is not confirmed.",
            )
        raise AssertionError(f"Unsupported structured schema: {schema}")

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if not self._tool_mode:
            raise AssertionError("The fake model was invoked without a schema")

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "TechnicalPlan",
                                "args": _technical_plan_payload(),
                                "id": "technical-plan-1",
                                "type": "tool_call",
                            }
                        ],
                    )
                )
            ]
        )


def fake_hypothesis_model(
    responses: list[str],
    *,
    sleep: float | None = None,
    uncertainties: list[str] | None = None,
    route: str = "archwise_workflow",
    direct_response: str = "",
) -> FakeWorkflowChatModel:
    """Create a deterministic model for the complete workflow."""

    return FakeWorkflowChatModel(
        responses,
        uncertainties=uncertainties,
        sleep=sleep,
        route=route,
        direct_response=direct_response,
    )


def archhypo_json(
    uncertainty: str,
    statement: str,
    *,
    index: int = 1,
) -> str:
    """Return the serialized complete result produced by the fake workflow."""

    return ArchHypo(
        uncertainty=uncertainty,
        hypothesis=Hypothesis(
            uncertainty=uncertainty,
            title=f"Hypothesis {index}",
            statement=statement,
            justification="Derived from the supplied uncertainty.",
        ),
        classification=_classification(),
        technical_plan=TechnicalPlan.model_validate(_technical_plan_payload()),
    ).model_dump_json(indent=2)


def hypothesis_json(
    uncertainty: str,
    statement: str,
    *,
    index: int = 1,
) -> str:
    """Return the serialized hypothesis agent response."""

    return Hypothesis(
        uncertainty=uncertainty,
        title=f"Hypothesis {index}",
        statement=statement,
        justification="Derived from the supplied uncertainty.",
    ).model_dump_json(indent=2)


def classification_json() -> str:
    """Return the serialized classifier response."""

    return _classification().model_dump_json(indent=2)


def technical_plan_json() -> str:
    """Return the serialized technical plan response."""

    return TechnicalPlan.model_validate(_technical_plan_payload()).model_dump_json(
        indent=2
    )


def _message_content(value: Any) -> str:
    if hasattr(value, "to_messages"):
        messages = value.to_messages()
    elif isinstance(value, dict):
        messages = value.get("messages", [])
    else:
        messages = []
    if not messages:
        return ""
    return str(getattr(messages[-1], "content", messages[-1]))


def _classification() -> HypothesisClassification:
    return HypothesisClassification(
        nfr="Performance",
        nfr_justification="The hypothesis concerns system capacity.",
        impact="High",
        impact_justification="Failure affects peak operation.",
        uncertainty="High",
        uncertainty_justification="The projected load is not confirmed.",
    )


def _technical_plan_payload() -> dict[str, Any]:
    return {
        "items": [
            {
                "title": "Run a benchmark",
                "objective": "Measure capacity",
                "description": "Use representative load",
                "pattern": "Learning from Experiments",
                "tradeoff": "Requires test effort",
            },
            {
                "title": "Set a checkpoint",
                "objective": "Verify performance",
                "description": "Define measurable limits",
                "pattern": "Quality Checkpoint",
                "tradeoff": "Adds process overhead",
            },
            {
                "title": "Define a trigger",
                "objective": "React to degradation",
                "description": "Review the architecture when capacity fails",
                "pattern": "Architectural Trigger",
                "tradeoff": "Requires agreed thresholds",
            },
        ],
        "rationale": "These actions generate evidence and guide the decision.",
    }


__all__ = [
    "FakeWorkflowChatModel",
    "archhypo_json",
    "classification_json",
    "fake_hypothesis_model",
    "hypothesis_json",
    "technical_plan_json",
]
