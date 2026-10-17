import json
from unittest.mock import Mock

import pytest
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime
from pydantic import ValidationError

from archhypo_flow_agent.core import (
    AgentState,
    ArchHypoResult,
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    HypothesisNovelty,
    HypothesisProposal,
    RequestRouting,
    TechnicalPlan,
)
from archhypo_flow_agent.graph.nodes import hypothesis_formulation as formulation
from archhypo_flow_agent.graph.nodes.direct_response_generation import (
    create_direct_response_generation_node,
)
from tests.fakes import structured_output

UNCERTAINTY = "Can a single server sustain the projected document ingestion rate?"
PREVIOUS_STATEMENT = "The single server cannot sustain the projected peak load."


def hypothesis(
    title="Single-server capacity is insufficient",
    statement=PREVIOUS_STATEMENT,
    uncertainty=UNCERTAINTY,
) -> Hypothesis:
    return Hypothesis(
        uncertainty=uncertainty,
        title=title,
        statement=statement,
        justification="This assumption can be investigated in the supplied scenario.",
    )


def result(item: Hypothesis) -> ArchHypoResult:
    return ArchHypoResult(
        uncertainty=item.uncertainty,
        discovery=ArchitecturalUncertaintyDiscovery(
            status="identified",
            uncertainty=item.uncertainty,
            rationale="The user supplied this capacity concern.",
        ),
        hypothesis=item,
        assessment=structured_output(HypothesisAssessment, {}),
        technical_plan=structured_output(TechnicalPlan, {}),
    )


def alternative_state() -> AgentState:
    previous = result(hypothesis())
    return {
        "messages": [HumanMessage(content="give me another hypothesis")],
        "routing": RequestRouting(intent="alternative_hypothesis"),
        "uncertainty": UNCERTAINTY,
        "discovery": previous.discovery,
        "hypothesis": previous.hypothesis,
        "assessment": previous.assessment,
        "technical_plan": previous.technical_plan,
        "result": previous,
        "result_history": [previous],
    }


def scripted_agents(monkeypatch, proposals, comparisons=()):
    generator = Mock()
    generator.invoke.side_effect = proposals
    verifier = Mock()
    verifier.invoke.side_effect = comparisons
    monkeypatch.setattr(
        formulation, "build_hypothesis_formulation_agent", lambda _: generator
    )
    monkeypatch.setattr(
        formulation, "build_hypothesis_novelty_agent", lambda _: verifier
    )
    return generator, verifier, formulation.create_hypothesis_formulation_node(Mock())


def distinct_claim() -> Hypothesis:
    return hypothesis(
        "Input format drives peak ingestion capacity",
        "The ingestion capacity differs between XML and JSON document batches.",
    )


def distinct() -> HypothesisNovelty:
    return HypothesisNovelty(
        is_distinct=True,
        rationale="The candidate tests format-dependent capacity, not total capacity.",
    )


def test_alternative_prompt_and_history_are_specific_to_the_active_uncertainty(
    monkeypatch,
) -> None:
    state = alternative_state()
    other = result(hypothesis("SSO support", "SSO is supported.", "SSO compatibility"))
    # Similar normalized wording is not enough to merge independent discoveries.
    other = other.model_copy(update={"uncertainty": UNCERTAINTY})
    state["result_history"].insert(0, other)
    candidate = distinct_claim().model_copy(
        update={"uncertainty": "A paraphrased concern"}
    )
    generator, verifier, node = scripted_agents(
        monkeypatch, [HypothesisProposal(hypothesis=candidate)], [distinct()]
    )

    update = node(state)

    prompt = generator.invoke.call_args.args[0]
    assert "Operation: alternative hypothesis" in prompt["system_prompt"]
    assert "Do not combine unrelated concerns or create alternatives" not in (
        prompt["system_prompt"]
    )
    assert "SSO support" not in prompt["material"]
    assert PREVIOUS_STATEMENT in prompt["material"]
    assert update["hypothesis"].statement == candidate.statement
    assert update["uncertainty"] == UNCERTAINTY
    assert update["hypothesis"].uncertainty == UNCERTAINTY
    assert update["result"] is None
    assert state["result"].hypothesis.statement == PREVIOUS_STATEMENT
    verifier.invoke.assert_called_once()


def test_renaming_the_same_statement_triggers_one_new_attempt(monkeypatch) -> None:
    repeated = hypothesis(
        "A different title",
        "  THE SINGLE SERVER cannot sustain the projected peak load.  ",
    )
    generator, verifier, node = scripted_agents(
        monkeypatch,
        [
            HypothesisProposal(hypothesis=repeated),
            HypothesisProposal(hypothesis=distinct_claim()),
        ],
        [distinct()],
    )

    update = node(alternative_state())

    assert update["hypothesis"].statement == distinct_claim().statement
    assert generator.invoke.call_count == 2
    assert "statement repeats" in generator.invoke.call_args.args[0]["material"]
    verifier.invoke.assert_called_once()


def test_a_semantic_paraphrase_is_not_accepted_as_an_alternative(monkeypatch) -> None:
    paraphrase = hypothesis(
        "Peak capacity constraint", "Peak load exceeds server capacity."
    )
    generator, verifier, node = scripted_agents(
        monkeypatch,
        [
            HypothesisProposal(hypothesis=paraphrase),
            HypothesisProposal(hypothesis=distinct_claim()),
        ],
        [
            HypothesisNovelty(is_distinct=False, rationale="Same capacity prediction."),
            distinct(),
        ],
    )

    update = node(alternative_state())

    assert update["hypothesis"].statement == distinct_claim().statement
    assert generator.invoke.call_count == verifier.invoke.call_count == 2
    retry_material = generator.invoke.call_args.args[0]["material"]
    assert "Same capacity prediction" in retry_material


def test_a_distinct_statement_should_not_reuse_the_review_title(monkeypatch) -> None:
    same_title = distinct_claim().model_copy(update={"title": hypothesis().title})
    generator, _, node = scripted_agents(
        monkeypatch,
        [
            HypothesisProposal(hypothesis=same_title),
            HypothesisProposal(hypothesis=distinct_claim()),
        ],
        [distinct()],
    )

    update = node(alternative_state())

    assert update["hypothesis"].title == distinct_claim().title
    assert generator.invoke.call_count == 2
    assert "title repeats" in generator.invoke.call_args.args[0]["material"]


def test_repeated_candidates_ask_a_question_not_another_review(monkeypatch) -> None:
    state = alternative_state()
    repeated = HypothesisProposal(hypothesis=hypothesis())
    generator, verifier, node = scripted_agents(monkeypatch, [repeated, repeated])

    update = node(state, Runtime(context={"language": "pt-BR"}))

    assert "hipótese realmente diferente" in update["formulation_question"]
    assert "hypothesis" not in update
    assert "result" not in update
    assert generator.invoke.call_count == 2
    verifier.invoke.assert_not_called()
    combined = {**state, **update}
    assert formulation.route_after_hypothesis_formulation(combined) == (
        "direct_response_generation"
    )
    response_agent = Mock()
    response = create_direct_response_generation_node(response_agent)(combined)
    response_agent.invoke.assert_not_called()
    assert response["messages"][0].content == update["formulation_question"]
    assert response["formulation_question"] is None


def test_semantic_repetitions_also_stop_after_two_attempts(monkeypatch) -> None:
    repeated_meaning = HypothesisProposal(
        hypothesis=hypothesis("Peak capacity constraint", "Peak load exceeds capacity.")
    )
    same_claim = HypothesisNovelty(
        is_distinct=False, rationale="The candidate makes the same prediction."
    )
    generator, verifier, node = scripted_agents(
        monkeypatch, [repeated_meaning, repeated_meaning], [same_claim, same_claim]
    )

    update = node(alternative_state())

    assert "Which other assumption" in update["formulation_question"]
    assert "hypothesis" not in update
    assert generator.invoke.call_count == verifier.invoke.call_count == 2


def test_generator_can_ask_instead_of_inventing_a_hypothesis(monkeypatch) -> None:
    question = "Which other assumption about ingestion should we investigate?"
    generator, verifier, node = scripted_agents(
        monkeypatch, [HypothesisProposal(clarification_question=question)]
    )

    update = node(alternative_state())

    assert update == {"formulation_question": question}
    generator.invoke.assert_called_once()
    verifier.invoke.assert_not_called()


def test_review_feedback_revises_the_candidate_not_the_approved_baseline(
    monkeypatch,
) -> None:
    state = alternative_state()
    state["hypothesis"] = distinct_claim()
    state["hypothesis_feedback"] = (
        "Explain the measurement without changing the claim."
    )
    revised = distinct_claim().model_copy(
        update={"justification": "Measure by format."}
    )
    generator, verifier, node = scripted_agents(
        monkeypatch, [HypothesisProposal(hypothesis=revised)], [distinct()]
    )

    update = node(state)

    assert "Operation: revision" in generator.invoke.call_args.args[0]["system_prompt"]
    comparison = json.loads(verifier.invoke.call_args.args[0]["material"])
    assert len(comparison["previous_hypotheses"]) == 1
    assert comparison["previous_hypotheses"][0]["statement"] == PREVIOUS_STATEMENT
    assert update["hypothesis"] == revised


@pytest.mark.parametrize("intent", ["new_uncertainty", "revise_hypothesis"])
def test_other_operations_skip_the_alternative_verifier(monkeypatch, intent) -> None:
    state = alternative_state()
    state["routing"] = RequestRouting(intent=intent)
    generator, verifier, node = scripted_agents(
        monkeypatch, [HypothesisProposal(hypothesis=hypothesis())]
    )

    update = node(state)

    assert update["hypothesis"] == hypothesis()
    operation = "initial formulation" if intent == "new_uncertainty" else "revision"
    prompt = generator.invoke.call_args.args[0]["system_prompt"]
    assert f"Operation: {operation}" in prompt
    verifier.invoke.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"clarification_question": "   "},
        {"hypothesis": hypothesis().model_dump(), "clarification_question": "Why?"},
    ],
)
def test_formulation_must_propose_a_hypothesis_or_ask_one_question(payload) -> None:
    with pytest.raises(ValidationError):
        HypothesisProposal.model_validate(payload)
