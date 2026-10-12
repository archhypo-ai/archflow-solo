from archhypo_flow_agent.stream import (
    ConversationStartedEvent,
    agent_event_data,
    done_event,
)


def test_conversation_started_event_contains_the_persisted_user_turn() -> None:
    event = ConversationStartedEvent(
        run_id="run-1",
        thread_id="thread-1",
        title="First question",
        user_message="First question",
        project_id=None,
    )

    assert agent_event_data(event) == {
        "protocol_version": 1,
        "run_id": "run-1",
        "thread_id": "thread-1",
        "type": "conversation_started",
        "title": "First question",
        "user_message": "First question",
        "project_id": None,
    }


def test_done_event_serializes_as_protocol_json() -> None:
    event = done_event(run_id="run-1", thread_id="thread-1")

    assert agent_event_data(event) == {
        "protocol_version": 1,
        "run_id": "run-1",
        "thread_id": "thread-1",
        "type": "done",
        "status": "completed",
    }
