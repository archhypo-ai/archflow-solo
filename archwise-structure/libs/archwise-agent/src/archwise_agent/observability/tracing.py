"""Optional LangSmith and Langfuse tracing integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from archwise_agent.config import AgentSettings, settings
from archwise_agent.core import ExecutionContext

logger = logging.getLogger(__name__)


class Observability:
    """Build tracing callbacks and metadata for one graph execution.

    Tracing is deliberately optional. If a provider is disabled, misconfigured,
    or unavailable, the ArchWise execution continues without callbacks.
    """

    def __init__(self, configuration: AgentSettings) -> None:
        self._configuration = configuration
        self._langsmith_client: Any | None = None
        self._langfuse_client: Any | None = None
        self._langfuse_handler_factory: Callable[..., Any] | None = None
        self._initialize_langsmith()
        self._initialize_langfuse()

    def graph_config(self, context: ExecutionContext) -> dict[str, Any]:
        """Return LangGraph config with callbacks and safe run metadata."""

        metadata = {
            "thread_id": context.thread_id,
            "workspace_id": context.workspace_id,
            "run_id": context.run_id,
        }
        if context.project_id is not None:
            metadata["project_id"] = context.project_id
        if context.user_id is not None:
            metadata["user_id"] = context.user_id

        config: dict[str, Any] = {
            "run_name": "archwise.workflow",
            "tags": ["archwise", "langgraph"],
            "metadata": metadata,
        }
        callbacks = self._callbacks()
        if callbacks:
            config["callbacks"] = callbacks
        return config

    def close(self) -> None:
        """Flush provider clients when the owning service shuts down."""

        for client in (self._langfuse_client, self._langsmith_client):
            flush = getattr(client, "flush", None)
            if callable(flush):
                try:
                    flush()
                except Exception:  # pragma: no cover - provider failure path
                    logger.warning(
                        "Unable to flush observability client.",
                        exc_info=True,
                    )

    def _callbacks(self) -> list[Any]:
        callbacks: list[Any] = []
        if self._langsmith_client is not None:
            try:
                from langchain_core.tracers import LangChainTracer

                callbacks.append(
                    LangChainTracer(
                        project_name=(
                            self._configuration.langsmith_project or "archwise"
                        ),
                        client=self._langsmith_client,
                    )
                )
            except Exception:  # pragma: no cover - provider failure path
                logger.warning(
                    "Unable to create the LangSmith tracing callback.",
                    exc_info=True,
                )

        if self._langfuse_handler_factory is not None:
            try:
                callbacks.append(
                    self._langfuse_handler_factory(
                        public_key=self._configuration.langfuse_public_key,
                    )
                )
            except Exception:  # pragma: no cover - provider failure path
                logger.warning(
                    "Unable to create the Langfuse tracing callback.",
                    exc_info=True,
                )
        return callbacks

    def _initialize_langsmith(self) -> None:
        configuration = self._configuration
        if not configuration.langsmith_tracing:
            return
        if not configuration.langsmith_api_key:
            logger.warning(
                "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is missing."
            )
            return

        try:
            from langsmith import Client

            self._langsmith_client = Client(
                api_url=configuration.langsmith_endpoint,
                api_key=configuration.langsmith_api_key,
            )
        except Exception:  # pragma: no cover - provider failure path
            logger.warning(
                "Unable to initialize LangSmith tracing. Continuing without LangSmith.",
                exc_info=True,
            )

    def _initialize_langfuse(self) -> None:
        configuration = self._configuration
        if not configuration.langfuse_enabled:
            return
        if not configuration.langfuse_public_key:
            logger.warning(
                "LANGFUSE_ENABLED is enabled but LANGFUSE_PUBLIC_KEY is missing."
            )
            return
        if not configuration.langfuse_secret_key:
            logger.warning(
                "LANGFUSE_ENABLED is enabled but LANGFUSE_SECRET_KEY is missing."
            )
            return

        try:
            from langfuse import Langfuse
            from langfuse.langchain import CallbackHandler

            self._langfuse_client = Langfuse(
                public_key=configuration.langfuse_public_key,
                secret_key=configuration.langfuse_secret_key,
                base_url=configuration.langfuse_base_url,
                tracing_enabled=True,
            )
            self._langfuse_handler_factory = CallbackHandler
        except Exception:  # pragma: no cover - optional dependency path
            logger.warning(
                "Unable to initialize Langfuse tracing."
                " Install the observability extra and check Python compatibility."
                " Continuing without Langfuse.",
                exc_info=True,
            )


def build_observability(
    configuration: AgentSettings | None = None,
) -> Observability:
    """Build optional tracing integrations from typed settings."""

    return Observability(configuration or settings)


__all__ = ["Observability", "build_observability"]
