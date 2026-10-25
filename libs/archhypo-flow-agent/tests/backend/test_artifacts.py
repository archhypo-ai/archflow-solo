from dataclasses import replace
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

    def get_by_id(self, artifact_id):
        return next(
            (record for record in self.records if record.id == artifact_id),
            None,
        )

    def update_status(self, artifact_id, status):
        for index, record in enumerate(self.records):
            if record.id == artifact_id:
                updated = replace(
                    record,
                    status=status,
                    updated_at=datetime.now(UTC).isoformat(),
                )
                self.records[index] = updated
                return updated
        return None


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
                "title": "Validate peak ingestion capacity",
                "justification": "A representative load test can measure capacity.",
                "statement": "One server can handle the projected load.",
            },
            "assessment": {
                "nfr": "Performance",
                "nfr_justification": "Throughput is the key quality attribute.",
                "impact": "High",
                "impact_justification": (
                    "A failure would require infrastructure changes."
                ),
                "uncertainty": "Medium",
                "uncertainty_justification": "The expected load is not measured yet.",
            },
            "technical_plan": {
                "rationale": "A load test can validate the capacity assumption.",
                "items": [
                    {
                        "title": "Replay a representative workload",
                        "objective": "Measure projected peak throughput.",
                        "description": "Replay a representative data batch.",
                        "pattern": "Architectural Spike",
                        "tradeoff": "Requires a representative test environment.",
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


def test_artifact_detail_returns_full_result_and_status_can_be_updated() -> None:
    review_history = [
        {
            "kind": "hypothesis_review",
            "review": {
                "kind": "hypothesis_review",
                "hypothesis": {
                    "title": "Validate peak ingestion capacity",
                    "statement": "One server can handle the projected load.",
                },
            },
            "decision": {
                "decision": "rejected",
                "reason": "Include a representative load test.",
            },
            "after_message_count": 1,
        }
    ]
    repository = InMemoryArtifactListRepository(
        [
            replace(
                artifact_record("artifact-1", project_id="project-1"),
                review_history=review_history,
            )
        ]
    )
    service = AgentService(
        checkpointer=MemorySaver(),
        artifact_repository=repository,
    )
    try:
        with TestClient(create_app(service)) as client:
            detail = client.get("/api/artifacts/artifact-1")
            updated = client.patch(
                "/api/artifacts/artifact-1",
                json={"status": "closed"},
            )
            listed = client.get("/api/artifacts")
            invalid_status = client.patch(
                "/api/artifacts/artifact-1",
                json={"status": "archived"},
            )
            missing = client.get("/api/artifacts/missing")

        assert detail.status_code == 200
        assert detail.json()["hypothesis"]["statement"] == (
            "One server can handle the projected load."
        )
        assert detail.json()["technical_plan"]["items"][0]["objective"] == (
            "Measure projected peak throughput."
        )
        assert detail.json()["technical_plan"]["items"][0]["pattern"] == (
            "Architectural Spike"
        )
        assert detail.json()["review_history"] == review_history
        assert updated.status_code == 200
        assert updated.json()["status"] == "closed"
        assert updated.json()["review_history"] == review_history
        assert listed.json()[0]["status"] == "closed"
        assert invalid_status.status_code == 422
        assert missing.status_code == 404
    finally:
        service.close()
