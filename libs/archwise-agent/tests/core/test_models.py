import pytest
from pydantic import ValidationError

from archwise_agent import (
    ArchHypo,
    Hypothesis,
    HypothesisClassification,
    TechnicalPlan,
)


def hypothesis() -> Hypothesis:
    return Hypothesis(
        uncertainty="Peak capacity is unknown.",
        title="Peak capacity",
        statement="The system handles the projected peak load.",
        justification="The assertion can be tested with a load experiment.",
    )


def classification() -> HypothesisClassification:
    return HypothesisClassification(
        nfr="Performance",
        nfr_justification="The issue concerns capacity.",
        impact="High",
        impact_justification="Failure affects peak operation.",
        uncertainty="High",
        uncertainty_justification="The projected load is not confirmed.",
    )


def plan() -> TechnicalPlan:
    item = {
        "title": "Run a benchmark",
        "objective": "Measure capacity",
        "description": "Use representative load",
        "pattern": "Learning from Experiments",
        "tradeoff": "Requires test effort",
    }
    return TechnicalPlan(
        items=[
            item,
            {**item, "title": "Set a checkpoint"},
            {**item, "title": "Define a trigger"},
        ],
        rationale="Generate evidence before deciding.",
    )


def test_complete_archhypo_contract_is_valid() -> None:
    result = ArchHypo(
        uncertainty="Peak capacity is unknown.",
        hypothesis=hypothesis(),
        classification=classification(),
        technical_plan=plan(),
    )

    assert result.hypothesis.uncertainty == result.uncertainty


def test_technical_plan_requires_one_to_three_items() -> None:
    with pytest.raises(ValidationError):
        TechnicalPlan(items=[], rationale="No plan")

    single_item = {
        "title": "Run a benchmark",
        "objective": "Measure capacity",
        "description": "Use representative load",
        "pattern": "Learning from Experiments",
        "tradeoff": "Requires test effort",
    }
    assert len(
        TechnicalPlan(items=[single_item], rationale="Generate evidence").items
    ) == 1

    with pytest.raises(ValidationError):
        TechnicalPlan(
            items=[single_item, single_item, single_item, single_item],
            rationale="Too many actions",
        )


def test_domain_models_are_immutable_and_forbid_extra_fields() -> None:
    value = hypothesis()

    with pytest.raises(ValidationError):
        value.title = "Changed"
    with pytest.raises(ValidationError):
        Hypothesis.model_validate(
            {
                **value.model_dump(),
                "unexpected": "field",
            }
        )
