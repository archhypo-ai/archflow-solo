from archwise_agent.config import AgentSettings
from archwise_agent.core import ExecutionContext
from archwise_agent.observability import build_observability


def test_observability_is_disabled_by_default() -> None:
    observability = build_observability(AgentSettings(_env_file=None))

    config = observability.graph_config(
        ExecutionContext(thread_id="thread-1", run_id="run-1")
    )

    assert "callbacks" not in config
    assert config["metadata"] == {
        "thread_id": "thread-1",
        "workspace_id": "default",
        "run_id": "run-1",
    }


def test_langsmith_callback_is_added_when_configured() -> None:
    observability = build_observability(
        AgentSettings(
            _env_file=None,
            langsmith_tracing=True,
            langsmith_api_key="test-key",
            langsmith_project="test-project",
        )
    )

    config = observability.graph_config(
        ExecutionContext(thread_id="thread-1", run_id="run-1")
    )

    assert len(config["callbacks"]) == 1


def test_missing_provider_credentials_do_not_break_execution() -> None:
    observability = build_observability(
        AgentSettings(
            _env_file=None,
            langsmith_tracing=True,
            langfuse_enabled=True,
        )
    )

    config = observability.graph_config(
        ExecutionContext(thread_id="thread-1", run_id="run-1")
    )

    assert "callbacks" not in config
