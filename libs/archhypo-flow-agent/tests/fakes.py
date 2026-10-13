"""Deterministic model stubs for service and API tests."""

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda

from archhypo_flow_agent.core import (
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    TechnicalPlan,
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
    if schema is Hypothesis:
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
    if schema is TechnicalPlan:
        return schema(
            items=[
                {
                    "title": "Run a focused spike",
                    "objective": "Collect evidence about the hypothesis.",
                    "description": "Test the assumption with a small experiment.",
                    "pattern": "Architectural Spike",
                    "tradeoff": "Requires a short, bounded investment.",
                }
            ],
            rationale="A small experiment can reduce uncertainty before commitment.",
        )
    raise AssertionError(f"Unsupported structured schema: {schema}")


__all__ = [
    "StructuredOutputStub",
    "StubChatModel",
    "structured_output",
    "stub_chat_model",
]
