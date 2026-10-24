from datetime import UTC, datetime

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.persistence.artifacts import ArchHypoArtifactRecord
from archhypo_flow_agent.services import AgentService


class InMemoryArtifactListRepository:
    def __init__(self, records: list[ArchHypoArtifactRecord]) -> None:
        self.records = records

    def list(self, *, project_id=None, thread_id=None):
        records = self.records
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if thread_id is not None:
            records = [record for record in records if record.thread_id == thread_id]
        return records


def artifact_record(
    artifact_id: str,
    *,
    project_id: str | None,
) -> ArchHypoArtifactRecord:
    return ArchHypoArtifactRecord(
        id=artifact_id,
        cycle_id=f"cycle-{artifact_id}",
        thread_id=f"thread-{artifact_id}",
        project_id=project_id,
        title="Validate peak ingestion capacity",
        status="open",
        outcome="not_evaluated",
        hitl_enabled=False,
        chat_model="test/chat-model",
        system_one_model="test/router-model",
        result_schema_version=1,
        routing={"intent": "new_uncertainty"},
        review_history=[],
        result={
            "uncertainty": "Can one server handle the projected load?",
            "hypothesis": {
                "statement": "One server can handle the projected load."
            },
            "assessment": {
                "nfr": "Performance",
                "impact": "High",
                "uncertainty": "Medium",
            },
            "technical_plan": {
                "items": [
                    {
                        "title": "Replay a representative workload",
                        "pattern": "Architectural Spike",
                    }
                ]
            },
        },
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )


def test_artifact_list_returns_card_summaries_and_filters_by_project() -> None:
    repository = InMemoryArtifactListRepository(
        [
            artifact_record("artifact-project", project_id="project-1"),
            artifact_record("artifact-unassigned", project_id=None),
        ]
    )
    service = AgentService(
        checkpointer=MemorySaver(),
        artifact_repository=repository,
    )
    try:
        with TestClient(create_app(service)) as client:
            all_artifacts = client.get("/api/artifacts")
            project_artifacts = client.get(
                "/api/artifacts",
                params={"project_id": "project-1"},
            )

        assert all_artifacts.status_code == 200
        assert len(all_artifacts.json()) == 2
        assert project_artifacts.status_code == 200
        assert len(project_artifacts.json()) == 1

        summary = project_artifacts.json()[0]
        assert summary["id"] == "artifact-project"
        assert summary["title"] == "Validate peak ingestion capacity"
        assert summary["status"] == "open"
        assert summary["nfr"] == "Performance"
        assert summary["impact"] == "High"
        assert summary["uncertainty_level"] == "Medium"
        assert summary["technical_plan_items"] == [
            {
                "title": "Replay a representative workload",
                "pattern": "Architectural Spike",
            }
        ]
    finally:
        service.close()
