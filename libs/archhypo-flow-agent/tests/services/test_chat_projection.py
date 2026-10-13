from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from archhypo_flow_agent.services.chat_projection import project_messages
from archhypo_flow_agent.services.conversation_service import _completed_reviews


def test_transcript_hides_legacy_synthetic_review_approval_messages() -> None:
    messages = [
        HumanMessage(content="Explore a database decision"),
        HumanMessage(
            content="I approve this hypothesis.\n\nKeep the rationale visible."
        ),
        HumanMessage(content="I approve this assessment and the technical plan."),
        AIMessage(content="The final recommendation is ready."),
    ]

    projected = project_messages(messages)

    assert [(message.role, message.content) for message in projected] == [
        ("user", "Explore a database decision"),
        ("assistant", "The final recommendation is ready."),
    ]


def test_legacy_checkpoint_approvals_are_restored_as_completed_cards() -> None:
    snapshot = SimpleNamespace(
        values={
            "messages": [
                HumanMessage(content="Explore a database decision"),
                HumanMessage(content="I approve this hypothesis."),
                HumanMessage(
                    content="I approve this assessment and the technical plan."
                ),
                AIMessage(content="The final recommendation is ready."),
            ],
            "hypothesis": {
                "uncertainty": "Database consistency is unclear.",
                "title": "Validate consistency",
                "statement": "The database preserves the required consistency.",
                "justification": "This can be tested.",
            },
            "hypothesis_review": {"decision": "approved"},
            "assessment": {
                "impact": "High",
                "impact_justification": "A change could affect many users.",
                "uncertainty": "Medium",
                "uncertainty_justification": "Some behavior is unverified.",
            },
            "technical_plan": {
                "rationale": "Test before committing.",
                "items": [
                    {
                        "title": "Run a consistency experiment",
                        "objective": "Verify data behavior.",
                        "description": "Exercise concurrent writes.",
                        "pattern": "Architectural Spike",
                        "tradeoff": "Requires a small test environment.",
                    }
                ],
            },
            "technical_plan_review": {"decision": "approved"},
        }
    )

    completed = _completed_reviews(snapshot)

    assert [review["kind"] for review in completed] == [
        "hypothesis_review",
        "technical_plan_review",
    ]
    assert [review["after_message_count"] for review in completed] == [1, 1]
