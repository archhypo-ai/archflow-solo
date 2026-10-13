"""Optional LangSmith and Langfuse tracing integrations."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from pydantic import SecretStr

from archhypo_flow_agent.config import AgentSettings, settings

logger = logging.getLogger(__name__)


class Observability:
    """Build optional tracing callbacks and safe metadata for graph runs."""

    def __init__(self, configuration: AgentSettings) -> None:
        self._configuration = configuration
        self._langsmith_client: Any | None = None
        self._langfuse_client: Any | None = None
        self._langfuse_handler_factory: Callable[..., Any] | None = None
        self._initialize_langsmith()
        self._initialize_langfuse()

    def graph_config(
        self,
        *,
        thread_id: str,
        run_id: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Return LangGraph tracing callbacks and identifiers for one turn."""

        metadata: dict[str, str] = {
            "thread_id": thread_id,
            "run_id": run_id,
        }
        if project_id is not None:
            metadata["project_id"] = project_id

        config: dict[str, Any] = {
            "run_name": "archhypo_flow.workflow",
            "tags": ["archhypo-flow", "langgraph"],
            "metadata": metadata,
        }
        callbacks = self._callbacks()
        if callbacks:
            config["callbacks"] = callbacks
        return config

    def close(self) -> None:
        """Flush provider clients when the owning agent service shuts down."""

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
                            self._configuration.langsmith_project or "archhypo-flow"
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
                public_key = self._secret_value(self._configuration.langfuse_public_key)
                callbacks.append(
                    self._langfuse_handler_factory(public_key=public_key)
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
        api_key = self._secret_value(configuration.langsmith_api_key)
        if not api_key:
            logger.warning(
                "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is missing."
            )
            return

        try:
            from langsmith import Client

            self._langsmith_client = Client(
                api_url=configuration.langsmith_endpoint,
                api_key=api_key,
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
        public_key = self._secret_value(configuration.langfuse_public_key)
        if not public_key:
            logger.warning(
                "LANGFUSE_ENABLED is enabled but LANGFUSE_PUBLIC_KEY is missing."
            )
            return
        secret_key = self._secret_value(configuration.langfuse_secret_key)
        if not secret_key:
            logger.warning(
                "LANGFUSE_ENABLED is enabled but LANGFUSE_SECRET_KEY is missing."
            )
            return

        try:
            from langfuse import Langfuse
            from langfuse.langchain import CallbackHandler

            self._langfuse_client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                base_url=configuration.langfuse_base_url,
                tracing_enabled=True,
            )
            self._langfuse_handler_factory = CallbackHandler
        except Exception:  # pragma: no cover - optional dependency path
            logger.warning(
                "Unable to initialize Langfuse tracing. Install the observability "
                "extra and check Python compatibility. Continuing without Langfuse.",
                exc_info=True,
            )

    @staticmethod
    def _secret_value(value: SecretStr | None) -> str | None:
        if value is None:
            return None
        return value.get_secret_value().strip() or None


def build_observability(
    configuration: AgentSettings | None = None,
) -> Observability:
    """Build optional tracing integrations from typed settings."""

    return Observability(configuration or settings)


__all__ = ["Observability", "build_observability"]
