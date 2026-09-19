"""LangGraph state for the ArchHypo workflow."""

from typing import Annotated, NotRequired

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .models import (
    ArchHypo,
    Hypothesis,
    HypothesisClassification,
    RequestRouting,
    TechnicalPlan,
)


class ArchHypoState(TypedDict):
    """State shared by the linear ArchHypo workflow."""

    messages: Annotated[list[AnyMessage], add_messages]
    uncertainty: str
    routing: NotRequired[RequestRouting]
    response: NotRequired[str]
    hypothesis: NotRequired[Hypothesis]
    classification: NotRequired[HypothesisClassification]
    technical_plan: NotRequired[TechnicalPlan]
    result: NotRequired[ArchHypo]


__all__ = ["ArchHypoState"]
