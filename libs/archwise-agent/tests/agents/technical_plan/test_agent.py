from langchain_core.messages import HumanMessage

from archwise_agent import TechnicalPlan, build_technical_plan_agent
from tests.fakes import fake_hypothesis_model


def test_technical_plan_agent_returns_a_catalog_grounded_plan() -> None:
    agent = build_technical_plan_agent(fake_hypothesis_model(["unused"]))

    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Architectural uncertainty: peak capacity is unknown.\n"
                        "Hypothesis: the system handles the projected load.\n"
                        "Classification: Performance, high impact, high uncertainty."
                    )
                )
            ]
        }
    )

    plan = result["structured_response"]
    assert isinstance(plan, TechnicalPlan)
    assert len(plan.items) == 3
    assert all(item.pattern for item in plan.items)
