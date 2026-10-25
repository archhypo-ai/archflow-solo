import json
import sqlite3

import pytest

from archhypo_flow_agent.core import (
    ArchHypoResult,
    ArchitecturalUncertaintyDiscovery,
    Hypothesis,
    HypothesisAssessment,
    RequestRouting,
    TechnicalPlan,
)
from archhypo_flow_agent.persistence import (
    ArtifactPersistenceError,
    open_sqlite_persistence,
)


def sample_result(
    title: str = "Validate document ingestion capacity",
) -> ArchHypoResult:
    uncertainty = "Can one server sustain the projected document ingestion rate?"
    return ArchHypoResult(
        uncertainty=uncertainty,
        discovery=ArchitecturalUncertaintyDiscovery(
            status="identified",
            uncertainty=uncertainty,
            rationale="The request contains an unresolved capacity decision.",
            missing_information=["Representative peak-load measurement"],
            confidence=0.91,
        ),
        hypothesis=Hypothesis(
            uncertainty=uncertainty,
            title=title,
            statement="A single server can sustain the projected peak rate.",
            justification="The expected ingestion rate can be measured in a spike.",
        ),
        assessment=HypothesisAssessment(
            nfr="Performance",
            nfr_justification="The concern centers on ingestion throughput.",
            impact="High",
            impact_justification=(
                "Insufficient capacity may force an infrastructure change."
            ),
            uncertainty="Medium",
            uncertainty_justification="The load is projected, not yet measured.",
        ),
        technical_plan=TechnicalPlan(
            rationale="A bounded load test can validate the throughput assumption.",
            items=[
                {
                    "title": "Measure peak ingestion",
                    "objective": "Test the expected document throughput.",
                    "description": "Replay representative XML and JSON batches.",
                    "pattern": "Architectural Spike",
                    "tradeoff": "Requires a representative test environment.",
                }
            ],
        ),
    )


def test_artifact_table_stores_the_exact_result_and_is_idempotent(tmp_path) -> None:
    persistence = open_sqlite_persistence(tmp_path / "artifacts.sqlite")
    try:
        persistence.projects.create(
            project_id="project-1",
            name="Document platform",
            icon="folder",
            color="blue",
            instructions="",
        )
        persistence.conversations.ensure("thread-1", "Capacity investigation")
        result = sample_result()
        routing = RequestRouting(intent="new_uncertainty")
        review_history = [
            {
                "kind": "hypothesis_review",
                "decision": {
                    "decision": "rejected",
                    "reason": "Make the hypothesis testable.",
                },
            },
            {
                "kind": "hypothesis_review",
                "decision": {"decision": "approved"},
            },
        ]
        fields = {
            "cycle_id": "cycle-1",
            "thread_id": "thread-1",
            "project_id": "project-1",
            "result": result,
            "routing": routing,
            "review_history": review_history,
            "hitl_enabled": True,
            "chat_model": "google/gemini-2.5-flash",
            "system_one_model": "typesafe/jev-1.14",
        }

        artifact_id = persistence.artifacts.save_final_result(**fields)
        retried_id = persistence.artifacts.save_final_result(**fields)

        assert retried_id == artifact_id
        assert len(persistence.artifacts.list()) == 1
        saved = persistence.artifacts.get_by_id(artifact_id)
        assert saved is not None
        assert saved.status == "open"
        assert saved.outcome == "not_evaluated"
        assert saved.hitl_enabled is True
        assert saved.routing == routing.model_dump(mode="json")
        assert saved.review_history == review_history
        assert saved.result == result.model_dump(mode="json")
        assert persistence.artifacts.list(project_id="project-1") == [saved]
        assert persistence.artifacts.list(thread_id="thread-1") == [saved]

        closed = persistence.artifacts.update_status(artifact_id, "closed")
        assert closed is not None
        assert closed.status == "closed"
        reopened = persistence.artifacts.update_status(artifact_id, "open")
        assert reopened is not None
        assert reopened.status == "open"
        assert persistence.artifacts.update_status("missing-artifact", "closed") is None

        with sqlite3.connect(tmp_path / "artifacts.sqlite") as connection:
            row = connection.execute(
                "SELECT result_json FROM archhypo_artifacts WHERE id = ?",
                (artifact_id,),
            ).fetchone()
        assert row is not None
        assert json.loads(row[0]) == result.model_dump(mode="json")

        with pytest.raises(ArtifactPersistenceError, match="different result snapshot"):
            persistence.artifacts.save_final_result(
                **{**fields, "result": sample_result("Changed title")}
            )
    finally:
        persistence.close()


def test_project_deletion_cascades_to_project_artifacts(tmp_path) -> None:
    persistence = open_sqlite_persistence(tmp_path / "delete-artifacts.sqlite")
    try:
        persistence.projects.create(
            project_id="project-1",
            name="Document platform",
            icon="folder",
            color="blue",
            instructions="",
        )
        persistence.conversations.ensure("thread-1", "Capacity investigation")
        artifact_id = persistence.artifacts.save_final_result(
            cycle_id="cycle-1",
            thread_id="thread-1",
            project_id="project-1",
            result=sample_result(),
            routing=RequestRouting(intent="new_uncertainty"),
            review_history=[],
            hitl_enabled=False,
            chat_model="test/chat-model",
            system_one_model="test/system-one-model",
        )

        assert persistence.delete_project("project-1") is True
        assert persistence.artifacts.get_by_id(artifact_id) is None
    finally:
        persistence.close()


def test_artifact_schema_creation_is_idempotent_without_migrations(tmp_path) -> None:
    database_path = tmp_path / "schema.sqlite"
    first = open_sqlite_persistence(database_path)
    first.close()
    second = open_sqlite_persistence(database_path)
    try:
        with sqlite3.connect(database_path) as connection:
            tables = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'archhypo_artifacts'"
            ).fetchall()
        assert tables == [("archhypo_artifacts",)]
    finally:
        second.close()
