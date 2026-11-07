import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import ValidationError

from archhypo_flow_agent.core import (
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    HypothesisProposal,
    HypothesisReview,
    RequestRouting,
    StructuredOutputError,
    TechnicalPlan,
    TechnicalPlanReview,
)
from archhypo_flow_agent.graph import build_graph as _build_graph
from archhypo_flow_agent.graph.nodes import technical_plan_generation
from archhypo_flow_agent.providers import SystemOneRequestError
from tests.fakes import (
    InMemoryArtifactRepository,
    StructuredOutputStub,
    StubSystemOneClient,
    structured_output,
)


def build_graph(model, **kwargs):
    kwargs.setdefault("artifact_repository", InMemoryArtifactRepository())
    kwargs.setdefault("chat_model_id", "test/chat-model")
    kwargs.setdefault("system_one_model_id", "test/system-one-model")
    return _build_graph(model, **kwargs)


class StubModel(StructuredOutputStub, FakeListChatModel):
    def __init__(self) -> None:
        super().__init__(responses=["Hello from the test agent."] * 20)

    def bind_tools(self, tools, **kwargs):
        return self


def test_graph_runs_the_minimum_archhypo_path_before_responding() -> None:
    system_one = StubSystemOneClient()
    artifacts = InMemoryArtifactRepository()
    graph = build_graph(
        model=StubModel(),
        system_one_client=system_one,
        artifact_repository=artifacts,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "approved-hypothesis"}}

    paused = graph.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config,
    )

    assert paused["hypothesis"].statement
    assert paused.get("assessment") is None
    assert graph.get_state(config).tasks[0].interrupts[0].value["kind"] == (
        "hypothesis_review"
    )
    assert artifacts.records == []

    plan_review = graph.invoke(
        Command(resume={"decision": "approved"}),
        config=config,
    )
    assert plan_review["assessment"].impact == "Medium"
    assert graph.get_state(config).tasks[0].interrupts[0].value["kind"] == (
        "technical_plan_review"
    )
    assert artifacts.records == []

    result = graph.invoke(
        Command(resume={"decision": "approved"}),
        config=config,
    )

    assert result["messages"][-1].content == "Hello from the test agent."
    assert system_one.calls == 1
    assert len(artifacts.records) == 1
    saved = artifacts.records[0]
    assert result["artifact_id"] == saved["id"]
    assert saved["cycle_id"] == result["cycle_id"]
    assert saved["result"] == result["result"]
    assert saved["hitl_enabled"] is True
    assert result["routing"].route == "architectural_uncertainty_discovery"
    assert result["discovery"].uncertainty == (
        "The architectural behavior is not yet confirmed."
    )
    assert result["hypothesis"].statement
    assert result["assessment"].impact == "Medium"
    assert result["technical_plan"].items[0].pattern == "Architectural Spike"
    assert [record["kind"] for record in result["review_history"]] == [
        "hypothesis_review",
        "technical_plan_review",
    ]
    graph_diagram = graph.get_graph().draw_mermaid()
    stages = [
        "request_routing",
        "documentary_research",
        "direct_response_generation",
        "architectural_uncertainty_discovery",
        "context_sufficiency_assessment",
        "hypothesis_formulation",
        "hypothesis_review",
        "hypothesis_assessment",
        "technical_plan_generation",
        "technical_plan_review",
        "artifact_persistence",
        "response_generation",
    ]
    assert all(stage in graph_diagram for stage in stages)
    assert set(graph.get_graph().nodes) == {
        "__start__",
        "__end__",
        *stages,
    }


@pytest.mark.parametrize("checkpointed", [False, True])
def test_disabled_hitl_runs_all_stages_without_human_approval(checkpointed) -> None:
    system_one = StubSystemOneClient()
    artifacts = InMemoryArtifactRepository()
    graph = build_graph(
        model=StubModel(),
        system_one_client=system_one,
        artifact_repository=artifacts,
        checkpointer=MemorySaver() if checkpointed else None,
    )
    config = {"configurable": {"thread_id": "without-human-review"}}

    result = graph.invoke(
        {"messages": [HumanMessage(content="Assess peak capacity.")]},
        config=config,
        context={"global_context": "", "project_context": "", "hitl_enabled": False},
    )

    assert result["messages"][-1].content == "Hello from the test agent."
    assert result["discovery"].uncertainty == "Assess peak capacity."
    assert result["hypothesis"].statement
    assert result["assessment"].impact == "Medium"
    assert result["technical_plan"].items[0].pattern == "Architectural Spike"
    assert result["result"].hypothesis == result["hypothesis"]
    assert result["hypothesis_review"] is None
    assert result["technical_plan_review"] is None
    assert result.get("review_history", []) == []
    assert not result.get("__interrupt__")
    assert system_one.calls == 1
    assert len(artifacts.records) == 1
    assert artifacts.records[0]["hitl_enabled"] is False
    if checkpointed:
        snapshot = graph.get_state(config)
        assert snapshot.next == ()
        assert not any(task.interrupts for task in snapshot.tasks)


def test_artifact_review_history_only_contains_its_cycle_decisions() -> None:
    artifacts = InMemoryArtifactRepository()
    graph = build_graph(
        model=StubModel(),
        system_one_client=StubSystemOneClient("new_uncertainty", "new_uncertainty"),
        artifact_repository=artifacts,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "review-history-cycles"}}

    graph.invoke(
        {"messages": [HumanMessage(content="Investigate first uncertainty.")]},
        config=config,
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    first_result = graph.invoke(
        Command(resume={"decision": "approved"}),
        config=config,
    )

    graph.invoke(
        {"messages": [HumanMessage(content="Investigate another uncertainty.")]},
        config=config,
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    second_result = graph.invoke(
        Command(resume={"decision": "approved"}),
        config=config,
    )

    assert first_result["cycle_id"] != second_result["cycle_id"]
    assert len(artifacts.records) == 2
    assert [
        record["cycle_id"] for record in artifacts.records[1]["review_history"]
    ] == [second_result["cycle_id"], second_result["cycle_id"]]
    assert len(second_result["review_history"]) == 4


def test_hitl_can_be_reenabled_for_the_next_turn() -> None:
    graph = build_graph(
        model=StubModel(),
        system_one_client=StubSystemOneClient(
            "new_uncertainty", "alternative_hypothesis"
        ),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "reenable-human-review"}}
    completed = graph.invoke(
        {"messages": [HumanMessage(content="Assess peak capacity.")]},
        config=config,
        context={"global_context": "", "project_context": "", "hitl_enabled": False},
    )

    graph.invoke(
        {"messages": [HumanMessage(content="Propose a different hypothesis.")]},
        config=config,
        context={"global_context": "", "project_context": "", "hitl_enabled": True},
    )
    snapshot = graph.get_state(config)
    assert snapshot.tasks[0].interrupts[0].value["kind"] == "hypothesis_review"
    assert snapshot.values["result_history"] == [completed["result"]]
    assert snapshot.values.get("review_history", []) == []

    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    result = graph.invoke(Command(resume={"decision": "approved"}), config=config)
    assert [record["kind"] for record in result["review_history"]] == [
        "hypothesis_review",
        "technical_plan_review",
    ]


def test_direct_question_keeps_the_completed_archhypo_result() -> None:
    graph = build_graph(
        model=StubModel(),
        checkpointer=MemorySaver(),
        system_one_client=StubSystemOneClient("new_uncertainty", "contextual_question"),
    )
    config = {"configurable": {"thread_id": "direct-follow-up"}}

    graph.invoke(
        {"messages": [HumanMessage(content="The service may not scale.")]},
        config=config,
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    completed = graph.invoke(Command(resume={"decision": "approved"}), config=config)
    completed_result = completed["result"]

    direct = graph.invoke(
        {"messages": [HumanMessage(content="Why is the impact rated Medium?")]},
        config=config,
    )

    assert direct["routing"].intent == "contextual_question"
    assert direct["routing"].route == "direct_response_generation"
    assert direct["result"] == completed_result
    assert direct["assessment"] == completed_result.assessment
    assert direct["messages"][-1].content == "Hello from the test agent."
    assert all(
        "archhypo_reference_context" not in str(message.content)
        for message in direct["messages"]
    )


def test_router_failure_preserves_the_previous_completed_result() -> None:
    system_one = StubSystemOneClient()
    graph = build_graph(
        model=StubModel(),
        system_one_client=system_one,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "failed-routing-follow-up"}}
    graph.invoke(
        {"messages": [HumanMessage(content="The service may not scale.")]},
        config=config,
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    completed = graph.invoke(Command(resume={"decision": "approved"}), config=config)

    system_one.error = SystemOneRequestError("decision service unavailable")
    with pytest.raises(SystemOneRequestError, match="service unavailable"):
        graph.invoke(
            {"messages": [HumanMessage(content="Gere outra hipótese")]},
            config=config,
        )

    snapshot = graph.get_state(config)
    assert snapshot.values["result"] == completed["result"]
    assert snapshot.values["hypothesis"] == completed["hypothesis"]
    assert snapshot.values["review_history"] == completed["review_history"]
    assert snapshot.values["messages"][-1].content == "Gere outra hipótese"
    assert snapshot.next == ("request_routing",)
    assert system_one.calls == 2


def test_unrepairable_assessment_keeps_approved_hypothesis_checkpoint() -> None:
    assessment_calls = [0]

    class MalformedAssessmentModel(StubModel):
        def with_structured_output(self, schema, **kwargs):
            if schema is HypothesisAssessment:

                def omit_required_justification(_input):
                    assessment_calls[0] += 1
                    return HypothesisAssessment.model_validate(
                        {
                            "nfr": "Performance",
                            "nfr_justification": "The input rate is large.",
                            "impact": "High",
                            "impact_justification": "Capacity affects deployment.",
                            "uncertainty": "Medium",
                        }
                    )

                return RunnableLambda(omit_required_justification)
            return super().with_structured_output(schema, **kwargs)

    model = MalformedAssessmentModel()
    graph = build_graph(
        model=model,
        system_one_client=StubSystemOneClient(),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "assessment-invalid-output"}}
    graph.invoke(
        {"messages": [HumanMessage(content="Assess peak capacity.")]},
        config=config,
    )

    with pytest.raises(StructuredOutputError, match="hypothesis_assessment"):
        graph.invoke(Command(resume={"decision": "approved"}), config=config)

    snapshot = graph.get_state(config)
    assert assessment_calls[0] == 2
    assert snapshot.values["hypothesis_review"].decision == "approved"
    assert snapshot.values["hypothesis"] is not None
    assert snapshot.values.get("assessment") is None
    assert [item["kind"] for item in snapshot.values["review_history"]] == [
        "hypothesis_review"
    ]


def test_alternative_hypothesis_preserves_prior_result_and_uncertainty() -> None:
    graph = build_graph(
        model=StubModel(),
        checkpointer=MemorySaver(),
        system_one_client=StubSystemOneClient(
            "new_uncertainty", "alternative_hypothesis"
        ),
    )
    config = {"configurable": {"thread_id": "alternative-hypothesis"}}
    graph.invoke(
        {"messages": [HumanMessage(content="The service may not scale.")]},
        config=config,
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    first_result = graph.invoke(
        Command(resume={"decision": "approved"}),
        config=config,
    )["result"]

    graph.invoke(
        {
            "messages": [
                HumanMessage(content="Propose another hypothesis for the same concern.")
            ]
        },
        config=config,
    )
    current = graph.get_state(config).values

    assert current["routing"].intent == "alternative_hypothesis"
    assert current["routing"].route == "hypothesis_formulation"
    assert current["result_history"] == [first_result]
    assert current["result"] is None
    assert current["uncertainty"] == first_result.uncertainty
    assert current["discovery"] == first_result.discovery
    assert current["hypothesis"].title == (
        "Alternative architectural behavior hypothesis"
    )
    assert graph.get_state(config).tasks[0].interrupts[0].value["kind"] == (
        "hypothesis_review"
    )


def test_repeated_alternative_does_not_create_another_approval_card() -> None:
    class RepeatingModel(StubModel):
        def with_structured_output(self, schema, **kwargs):
            if schema is HypothesisProposal:
                return RunnableLambda(
                    lambda _: HypothesisProposal(
                        hypothesis=structured_output(Hypothesis, {})
                    )
                )
            return super().with_structured_output(schema, **kwargs)

    system_one = StubSystemOneClient("new_uncertainty", "alternative_hypothesis")
    graph = build_graph(
        model=RepeatingModel(),
        system_one_client=system_one,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "repeated-alternative"}}
    graph.invoke(
        {"messages": [HumanMessage(content="Investigate peak ingestion capacity.")]},
        config=config,
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    completed = graph.invoke(Command(resume={"decision": "approved"}), config=config)

    clarified = graph.invoke(
        {"messages": [HumanMessage(content="give me another hypothesis")]},
        config=config,
    )

    assert graph.get_state(config).next == ()
    assert clarified["result"] == completed["result"]
    assert clarified["hypothesis"] == completed["hypothesis"]
    assert clarified["assessment"] == completed["assessment"]
    assert clarified["review_history"] == completed["review_history"]
    assert clarified["messages"][-1].type == "ai"
    assert "Which other assumption" in clarified["messages"][-1].content
    assert system_one.calls == 2


def test_concrete_uncertainty_classification_enters_archhypo_flow() -> None:
    system_one = StubSystemOneClient("new_uncertainty")
    graph = build_graph(
        model=StubModel(),
        checkpointer=MemorySaver(),
        system_one_client=system_one,
    )
    config = {"configurable": {"thread_id": "classify-concrete-uncertainty"}}
    message = (
        "Classify the central quality domain for this public-agency document "
        "system. The projected peak may reach 1 GB/minute, and the team is "
        "uncertain whether the current single-server architecture can sustain "
        "that load. The note also mentions legacy XML/JSON and SSO integration."
    )

    paused = graph.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    assert system_one.state["latest_user_message"] == message
    new_uncertainty_criteria = system_one.questions["intent"]["criteria"][
        "new_uncertainty"
    ]
    assert "central quality domain" in new_uncertainty_criteria
    assert "projected peak throughput" in new_uncertainty_criteria
    assert paused["routing"].intent == "new_uncertainty"
    assert paused["routing"].route == "architectural_uncertainty_discovery"
    assert paused["discovery"] is not None
    assert graph.get_state(config).tasks[0].interrupts[0].value["kind"] == (
        "hypothesis_review"
    )


@pytest.mark.parametrize(
    ("intent", "route"),
    [
        ("new_uncertainty", "architectural_uncertainty_discovery"),
        ("alternative_hypothesis", "hypothesis_formulation"),
        ("revise_hypothesis", "hypothesis_formulation"),
        ("contextual_question", "direct_response_generation"),
        ("out_of_scope", "direct_response_generation"),
        ("clarification", "direct_response_generation"),
    ],
)
def test_request_intent_maps_to_its_graph_destination(intent, route) -> None:
    assert RequestRouting(intent=intent).route == route


def test_legacy_route_checkpoint_is_upgraded_to_request_intent() -> None:
    routing = RequestRouting.model_validate({"route": "direct_response_generation"})

    assert routing.intent == "contextual_question"

    with pytest.raises(ValidationError):
        RequestRouting.model_validate({})


def test_rejected_hypothesis_is_reformulated_using_required_feedback() -> None:
    graph = build_graph(
        model=StubModel(),
        system_one_client=StubSystemOneClient(),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "rejected-hypothesis"}}
    initial = graph.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config,
    )
    first_statement = initial["hypothesis"].statement

    graph.invoke(
        Command(
            resume={
                "decision": "rejected",
                "reason": "Make the statement directly testable.",
            }
        ),
        config=config,
    )
    revised = graph.get_state(config).values["hypothesis"]

    assert revised.statement != first_statement
    assert "Make the statement directly testable." in revised.statement
    assert graph.get_state(config).values.get("assessment") is None
    rejected_history = graph.get_state(config).values["review_history"]
    assert len(rejected_history) == 1
    assert rejected_history[0]["decision"] == {
        "decision": "rejected",
        "reason": "Make the statement directly testable.",
    }

    second_statement = revised.statement
    graph.invoke(
        Command(
            resume={
                "decision": "rejected",
                "reason": "Include a rollback criterion.",
            }
        ),
        config=config,
    )
    revised_again = graph.get_state(config).values["hypothesis"]
    assert revised_again.statement != second_statement
    assert [
        record["decision"]["reason"]
        for record in graph.get_state(config).values["review_history"]
    ] == [
        "Make the statement directly testable.",
        "Include a rollback criterion.",
    ]

    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    assert graph.get_state(config).values["assessment"].impact == "Medium"
    assert graph.get_state(config).tasks[0].interrupts[0].value["kind"] == (
        "technical_plan_review"
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    assert graph.get_state(config).next == ()
    assert [
        record["kind"] for record in graph.get_state(config).values["review_history"]
    ] == [
        "hypothesis_review",
        "hypothesis_review",
        "hypothesis_review",
        "technical_plan_review",
    ]
    assert [
        record["decision"]["decision"]
        for record in graph.get_state(config).values["review_history"]
    ] == ["rejected", "rejected", "approved", "approved"]


def test_rejected_technical_plan_is_regenerated_with_feedback() -> None:
    artifacts = InMemoryArtifactRepository()
    graph = build_graph(
        model=StubModel(),
        system_one_client=StubSystemOneClient(),
        artifact_repository=artifacts,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "rejected-technical-plan"}}
    graph.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config=config,
    )
    graph.invoke(Command(resume={"decision": "approved"}), config=config)
    first_state = graph.get_state(config)
    first_assessment = first_state.values["assessment"]
    first_plan = first_state.values["technical_plan"]
    assert first_state.tasks[0].interrupts[0].value["kind"] == ("technical_plan_review")
    assert artifacts.records == []

    graph.invoke(
        Command(
            resume={
                "decision": "rejected",
                "reason": "Add evidence that can trigger a rollback.",
            }
        ),
        config=config,
    )

    revised_state = graph.get_state(config)
    revised_plan = revised_state.values["technical_plan"]
    assert revised_state.values["assessment"] == first_assessment
    assert revised_plan != first_plan
    assert "Add evidence that can trigger a rollback." in (
        revised_plan.items[0].description
    )
    assert revised_state.tasks[0].interrupts[0].value["kind"] == (
        "technical_plan_review"
    )
    assert revised_state.values["review_history"][-1]["decision"] == {
        "decision": "rejected",
        "reason": "Add evidence that can trigger a rollback.",
    }
    assert artifacts.records == []
    reviewed_payload = revised_state.tasks[0].interrupts[0].value
    assert (
        "Add evidence that can trigger a rollback."
        in reviewed_payload["technical_plan"]["items"][0]["description"]
    )

    result = graph.invoke(Command(resume={"decision": "approved"}), config=config)
    assert result["messages"][-1].content == "Hello from the test agent."
    assert len(artifacts.records) == 1
    assert artifacts.records[0]["result"] == result["result"]
    assert artifacts.records[0]["review_history"] == result["review_history"]
    assert [record["kind"] for record in result["review_history"]] == [
        "hypothesis_review",
        "technical_plan_review",
        "technical_plan_review",
    ]
    assert [record["decision"]["decision"] for record in result["review_history"]] == [
        "approved",
        "rejected",
        "approved",
    ]


def test_rejection_requires_a_reason() -> None:
    with pytest.raises(ValidationError, match="reason is required"):
        HypothesisReview(decision="rejected")
    with pytest.raises(ValidationError, match="reason is required"):
        TechnicalPlanReview(decision="rejected")


def test_technical_plan_cannot_use_an_unread_catalog_pattern(monkeypatch) -> None:
    class InvalidPlanner:
        def invoke(self, _input):
            return TechnicalPlan(
                items=[
                    {
                        "title": "Trace the system",
                        "objective": "Collect evidence about behavior.",
                        "description": "Follow the behavior end to end.",
                        "pattern": "Tracer Bullets",
                        "tradeoff": "Requires a focused implementation effort.",
                    }
                ],
                rationale="A tracer bullet can gather evidence.",
            )

    monkeypatch.setattr(
        technical_plan_generation,
        "build_technical_plan_generation_agent",
        lambda _model: InvalidPlanner(),
    )
    node = technical_plan_generation.create_technical_plan_generation_node(
        StructuredOutputStub()
    )
    state = {
        "uncertainty": "The system behavior has not been validated.",
        "discovery": ArchitecturalUncertaintyDiscovery(
            status="identified",
            uncertainty="The system behavior has not been validated.",
            rationale="The user identified an unknown system behavior.",
        ),
        "hypothesis": Hypothesis(
            uncertainty="The system behavior has not been validated.",
            title="Validate system behavior",
            statement="The system meets the stated behavior.",
            justification="This is a testable statement.",
        ),
        "assessment": HypothesisAssessment(
            nfr="Reliability",
            nfr_justification="The concern relates to reliable behavior.",
            impact="Medium",
            impact_justification="Changing the architecture may require rework.",
            uncertainty="High",
            uncertainty_justification="The hypothesis has not been tested.",
        ),
    }

    with pytest.raises(ValueError, match="without reading their catalog references"):
        node(state)
