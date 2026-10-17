"""Deterministic model stubs for service and API tests."""

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda

from archhypo_flow_agent.core import (
    ArchitecturalUncertaintyDiscovery,
    CatalogPatternSelection,
    ChatRequest,
    Hypothesis,
    HypothesisAssessment,
    HypothesisReview,
    RequestRouting,
    TechnicalPlan,
    TechnicalPlanReview,
)


class StructuredOutputStub:
    def with_structured_output(self, schema, **kwargs):
        return RunnableLambda(lambda value: structured_output(schema, value))


class StubChatModel(StructuredOutputStub, FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def stub_chat_model(
    message: str = "Understood. Let's explore this architectural decision.",
) -> StubChatModel:
    responses = [
        AIMessage(content=message, id=f"stub-response-{index}") for index in range(100)
    ]
    return StubChatModel(responses=responses)


def approved_hypothesis_request(
    thread_id: str,
    *,
    project_id: str | None = None,
    global_context: str = "",
) -> ChatRequest:
    return ChatRequest(
        thread_id=thread_id,
        message="",
        project_id=project_id,
        global_context=global_context,
        hypothesis_review=HypothesisReview(decision="approved"),
    )


def approved_technical_plan_request(
    thread_id: str,
    *,
    project_id: str | None = None,
    global_context: str = "",
) -> ChatRequest:
    return ChatRequest(
        thread_id=thread_id,
        message="",
        project_id=project_id,
        global_context=global_context,
        technical_plan_review=TechnicalPlanReview(decision="approved"),
    )


def structured_output(schema, value):
    if hasattr(value, "to_messages"):
        messages = value.to_messages()
    elif isinstance(value, dict):
        messages = value.get("messages", [])
    else:
        messages = []

    if schema is ArchitecturalUncertaintyDiscovery:
        latest = next(
            (
                message.content
                for message in reversed(messages)
                if isinstance(message, HumanMessage)
            ),
            "User input",
        )
        if not isinstance(latest, str):
            latest = "User input"
        return schema(
            status="identified",
            uncertainty=latest,
            rationale="The stub reuses the user-provided concern.",
            confidence=0.9,
        )
    if schema is RequestRouting:
        return RequestRouting(intent="new_uncertainty")
    if schema is Hypothesis:
        material = _human_material(value)
        marker = "Reviewer feedback (address this directly):\n"
        if marker in material:
            feedback = material.split(marker, maxsplit=1)[1].strip()
            return schema(
                uncertainty="The architectural behavior is not yet confirmed.",
                title="Revised architectural behavior hypothesis",
                statement=f"The system addresses the reviewer feedback: {feedback}",
                justification=(
                    "The hypothesis was revised to address the user's reason."
                ),
            )
        if "Previously proposed hypotheses for this uncertainty" in material:
            return schema(
                uncertainty="The architectural behavior is not yet confirmed.",
                title="Alternative architectural behavior hypothesis",
                statement=(
                    "An alternative implementation meets the user-visible behavior."
                ),
                justification=(
                    "This is a distinct testable alternative for the same uncertainty."
                ),
            )
        if "Hypothesis to revise" in material:
            return schema(
                uncertainty="The architectural behavior is not yet confirmed.",
                title="Revised architectural behavior hypothesis",
                statement=(
                    "The revised hypothesis accounts for the requested constraint."
                ),
                justification="The previous hypothesis was revised as requested.",
            )
        return schema(
            uncertainty="The architectural behavior is not yet confirmed.",
            title="Confirm the architectural behavior",
            statement="The system can meet the behavior described by the user.",
            justification="This is a testable statement for the supplied concern.",
        )
    if schema is HypothesisAssessment:
        return schema(
            nfr="Flexibility",
            nfr_justification="The uncertainty concerns the ability to adapt.",
            impact="Medium",
            impact_justification="Changing the decision may require some rework.",
            uncertainty="High",
            uncertainty_justification="The hypothesis has not been validated.",
        )
    if schema is CatalogPatternSelection:
        return schema(
            candidate_patterns=[
                "Architectural Spike",
                "Learning from Experiments",
                "Tracer Bullets",
            ],
            selected_patterns=["Architectural Spike"],
            rationale="A bounded experiment best addresses the stated uncertainty.",
        )
    if schema is TechnicalPlan:
        material = _human_material(value)
        marker = "Human review feedback (address this directly):\n"
        feedback = (
            material.split(marker, maxsplit=1)[1].strip()
            if marker in material
            else ""
        )
        description = "Test the assumption with a small experiment."
        rationale = "A small experiment can reduce uncertainty before commitment."
        if feedback:
            description += f" The revision addresses: {feedback}"
            rationale += f" Reviewer feedback: {feedback}"
        return schema(
            items=[
                {
                    "title": "Run a focused spike",
                    "objective": "Collect evidence about the hypothesis.",
                    "description": description,
                    "pattern": "Architectural Spike",
                    "tradeoff": "Requires a short, bounded investment.",
                }
            ],
            rationale=rationale,
        )
    raise AssertionError(f"Unsupported structured schema: {schema}")


def _human_material(value) -> str:
    messages = value.to_messages() if hasattr(value, "to_messages") else []
    for message in reversed(messages):
        if isinstance(message, HumanMessage) and isinstance(message.content, str):
            return message.content
    return ""


__all__ = [
    "StructuredOutputStub",
    "StubChatModel",
    "approved_hypothesis_request",
    "approved_technical_plan_request",
    "structured_output",
    "stub_chat_model",
]
