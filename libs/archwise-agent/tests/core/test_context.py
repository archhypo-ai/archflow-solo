import pytest

from archwise_agent.core import DEFAULT_WORKSPACE_ID, ExecutionContext


def test_execution_context_keeps_identity_outside_message_history() -> None:
    context = ExecutionContext(thread_id="thread-1")

    assert context.workspace_id == DEFAULT_WORKSPACE_ID
    assert context.project_id is None
    assert context.user_id is None
    assert context.run_id
    assert context.as_graph_context()["thread_id"] == "thread-1"


def test_execution_context_rejects_blank_identity() -> None:
    with pytest.raises(ValueError, match="workspace_id"):
        ExecutionContext(thread_id="thread-1", workspace_id=" ")
