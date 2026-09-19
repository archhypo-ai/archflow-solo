from langchain_core.messages import AIMessage, HumanMessage

from archwise_agent.agents.orchestrator.nodes.response_composition_node import (
    response_history,
)
from archwise_agent.services.conversation_projection import user_visible_messages

PASTED_PROMPT = """
You are an expert classifier.
{input}
A long user document.
{/input}
""".strip()


def test_pasted_prompt_markers_do_not_hide_user_message() -> None:
    messages = [HumanMessage(content=PASTED_PROMPT)]

    projected = user_visible_messages(messages)
    history = response_history(messages)

    assert [message.content for message in projected] == [PASTED_PROMPT]
    assert [message.content for message in history] == [PASTED_PROMPT]


def test_named_workflow_messages_remain_hidden() -> None:
    messages = [
        HumanMessage(content="User uncertainty"),
        AIMessage(
            name="hypothesis_formulator_agent",
            content='{"statement":"internal"}',
        ),
    ]

    projected = user_visible_messages(messages)
    history = response_history(messages)

    assert projected == [messages[0]]
    assert history == [messages[0]]
