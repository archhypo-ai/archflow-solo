"""Test doubles for structured ArchWise agent responses."""

import json
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from archwise_agent.core import ArchHypo, Hypothesis


class FakeHypothesisChatModel(FakeListChatModel):
    """Fake model with the structured-output capability used in production."""

    def with_structured_output(
        self,
        schema: Any,
        **kwargs: Any,
    ):
        return self | RunnableLambda(
            lambda message: schema.model_validate_json(message.content)
        )


def fake_hypothesis_model(
    responses: list[str],
    *,
    sleep: float | None = None,
) -> FakeHypothesisChatModel:
    """Create fixed Pydantic responses from hypothesis statements."""

    payloads = [
        (
            "{"
            f'"title":"Hypothesis {index}",'
            f'"statement":{_json_string(statement)},'
            '"justification":"Derived from the supplied uncertainty."'
            "}"
        )
        for index, statement in enumerate(responses, start=1)
    ]
    return FakeHypothesisChatModel(
        responses=payloads,
        sleep=sleep,
        disable_streaming=True,
    )


def archhypo_json(
    uncertainty: str,
    statement: str,
    *,
    index: int = 1,
) -> str:
    """Return the assistant message produced by the orchestrator."""

    return ArchHypo(
        uncertainty=uncertainty,
        hypothesis=Hypothesis(
            title=f"Hypothesis {index}",
            statement=statement,
            justification="Derived from the supplied uncertainty.",
        ),
    ).model_dump_json(indent=2)


def _json_string(value: str) -> str:
    return json.dumps(value)
