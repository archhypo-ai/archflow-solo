from __future__ import annotations

import sys
from threading import Lock
from types import ModuleType, SimpleNamespace
from typing import Any

from langchain_core import tracers
from langchain_core.messages import AIMessage
from pydantic import SecretStr

from archhypo_flow_agent.config import AgentSettings
from archhypo_flow_agent.core import ChatRequest
from archhypo_flow_agent.observability import build_observability
from archhypo_flow_agent.services.chat_context import ChatContextResolver
from archhypo_flow_agent.services.chat_execution import ChatExecutionService


def test_observability_is_disabled_by_default() -> None:
    observability = build_observability(AgentSettings(_env_file=None))

    config = observability.graph_config(
        thread_id="thread-1",
        run_id="run-1",
    )

    assert "callbacks" not in config
    assert config["metadata"] == {"thread_id": "thread-1", "run_id": "run-1"}
    assert config["run_name"] == "archhypo_flow.workflow"


def test_both_tracing_providers_can_be_enabled(
    monkeypatch,
) -> None:
    created: dict[str, Any] = {}

    class FakeLangSmithClient:
        def __init__(self, **kwargs: object) -> None:
            created["langsmith_client_kwargs"] = kwargs
            self.flush_count = 0
            created["langsmith_client"] = self

        def flush(self) -> None:
            self.flush_count += 1

    class FakeLangfuseClient:
        def __init__(self, **kwargs: object) -> None:
            created["langfuse_client_kwargs"] = kwargs
            self.flush_count = 0
            created["langfuse_client"] = self

        def flush(self) -> None:
            self.flush_count += 1

    class FakeLangfuseHandler:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    langsmith_module = ModuleType("langsmith")
    langsmith_module.Client = FakeLangSmithClient  # type: ignore[attr-defined]
    langfuse_module = ModuleType("langfuse")
    langfuse_module.__path__ = []  # type: ignore[attr-defined]
    langfuse_module.Langfuse = FakeLangfuseClient  # type: ignore[attr-defined]
    langfuse_langchain_module = ModuleType("langfuse.langchain")
    langfuse_langchain_module.CallbackHandler = FakeLangfuseHandler  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "langsmith", langsmith_module)
    monkeypatch.setitem(sys.modules, "langfuse", langfuse_module)
    monkeypatch.setitem(sys.modules, "langfuse.langchain", langfuse_langchain_module)

    class FakeLangChainTracer:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    monkeypatch.setattr(tracers, "LangChainTracer", FakeLangChainTracer)

    observability = build_observability(
        AgentSettings(
            _env_file=None,
            langsmith_tracing=True,
            langsmith_endpoint="https://smith.example.test",
            langsmith_api_key=SecretStr("smith-key"),
            langsmith_project="archhypo-tests",
            langfuse_enabled=True,
            langfuse_secret_key=SecretStr("langfuse-secret"),
            langfuse_public_key=SecretStr("langfuse-public"),
            langfuse_base_url="https://langfuse.example.test",
        )
    )

    config = observability.graph_config(
        thread_id="thread-1",
        run_id="run-1",
        project_id="project-1",
    )

    assert config["metadata"] == {
        "thread_id": "thread-1",
        "run_id": "run-1",
        "project_id": "project-1",
    }
    callbacks = config["callbacks"]
    assert len(callbacks) == 2
    assert callbacks[0].kwargs["project_name"] == "archhypo-tests"
    assert callbacks[1].kwargs == {"public_key": "langfuse-public"}
    assert created["langsmith_client_kwargs"] == {
        "api_url": "https://smith.example.test",
        "api_key": "smith-key",
    }
    assert created["langfuse_client_kwargs"] == {
        "public_key": "langfuse-public",
        "secret_key": "langfuse-secret",
        "base_url": "https://langfuse.example.test",
        "tracing_enabled": True,
    }

    observability.close()
    assert created["langsmith_client"].flush_count == 1
    assert created["langfuse_client"].flush_count == 1


def test_missing_provider_credentials_do_not_break_execution() -> None:
    observability = build_observability(
        AgentSettings(
            _env_file=None,
            langsmith_tracing=True,
            langfuse_enabled=True,
        )
    )

    config = observability.graph_config(
        thread_id="thread-1",
        run_id="run-1",
    )

    assert "callbacks" not in config


def test_chat_execution_passes_trace_config_to_graph() -> None:
    class RecordingGraph:
        config: dict[str, object] | None = None

        def get_state(self, _config: dict[str, object]) -> SimpleNamespace:
            return SimpleNamespace(values={"messages": []})

        def update_state(self, *_args: object, **_kwargs: object) -> None:
            return None

        def invoke(
            self,
            _input: dict[str, object],
            *,
            config: dict[str, object],
            context: dict[str, object],
        ) -> dict[str, object]:
            self.config = config
            return {"messages": [AIMessage(content="Reply")], "context": context}

    graph = RecordingGraph()
    execution = ChatExecutionService(
        graph,
        ChatContextResolver(None, None),
        Lock(),
        build_observability(AgentSettings(_env_file=None)),
    )

    execution.respond(ChatRequest(thread_id="thread-1", message="Hello"))

    assert graph.config is not None
    assert graph.config["configurable"] == {"thread_id": "thread-1"}
    metadata = graph.config["metadata"]
    assert metadata["thread_id"] == "thread-1"
    assert isinstance(metadata["run_id"], str) and metadata["run_id"]
