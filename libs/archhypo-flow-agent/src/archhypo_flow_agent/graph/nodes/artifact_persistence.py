"""Persist the approved/bypassed ArchHypo result before the final reply."""

from langchain_core.runnables import RunnableConfig

from archhypo_flow_agent.core import AgentState
from archhypo_flow_agent.persistence import (
    ArchHypoArtifactRepository,
    ArtifactPersistenceError,
)


def create_artifact_persistence_node(
    repository: ArchHypoArtifactRepository,
    *,
    chat_model: str | None,
    system_one_model: str | None,
):
    """Create an idempotent data node; graph code never opens the database."""

    def persist(
        state: AgentState,
        config: RunnableConfig,
    ) -> dict[str, object]:
        result = state.get("result")
        routing = state.get("routing")
        cycle_id = state.get("cycle_id")
        configurable = config.get("configurable", {})
        thread_id = (
            configurable.get("thread_id")
            if isinstance(configurable, dict)
            else None
        )
        if result is None or routing is None or not cycle_id or not thread_id:
            raise ArtifactPersistenceError(
                "A final result, route, cycle ID, and thread ID are required "
                "before persisting an ArchHypo artifact"
            )

        artifact_id = repository.save_final_result(
            cycle_id=cycle_id,
            thread_id=str(thread_id),
            project_id=state.get("project_id"),
            result=result,
            routing=routing,
            review_history=[
                review
                for review in state.get("review_history", [])
                if isinstance(review, dict) and review.get("cycle_id") == cycle_id
            ],
            hitl_enabled=state.get("hitl_enabled", True),
            chat_model=chat_model,
            system_one_model=system_one_model,
        )
        return {"artifact_id": artifact_id}

    return persist


__all__ = ["create_artifact_persistence_node"]
