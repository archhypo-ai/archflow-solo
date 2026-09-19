from pathlib import Path

from archwise_agent.tools.catalog import CatalogReader

CATALOG_ROOT = Path(__file__).resolve().parents[2] / "skills" / "archhypo-catalog"


def test_catalog_index_contains_only_canonical_related_patterns() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    entries = {entry.name: entry for entry in reader.index()}

    assert entries["Architectural Spike"].related_patterns == (
        "Bring the Specialist",
        "Technical Debt Management",
        "Tracer Bullets",
    )
    assert entries["Technical Debt Management"].related_patterns == (
        "Architectural Spike",
        "Architectural Trigger",
        "Continuous Inspection",
    )


def test_catalog_reader_deduplicates_within_one_graph_run() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    first = reader.read(
        run_id="run-1",
        patterns=["Architectural Spike", "Protective Guideline"],
    )
    second = reader.read(
        run_id="run-1",
        patterns=["Architectural Spike", "Continuous Inspection"],
    )

    assert first["read_now"] == ["Architectural Spike", "Protective Guideline"]
    assert second["read_now"] == ["Continuous Inspection"]
    assert second["skipped_already_read"] == ["Architectural Spike"]


def test_catalog_reader_isolates_runs_and_enforces_reference_budget() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    first = reader.read(run_id="run-1", patterns=["Architectural Spike"])
    second = reader.read(run_id="run-2", patterns=["Architectural Spike"])
    selected = reader.read(
        run_id="run-3",
        patterns=[
            "Architectural Spike",
            "Quality Checkpoint",
            "Technical Debt Management",
        ],
    )
    overflow = reader.read(run_id="run-3", patterns=["Continuous Inspection"])

    assert first["read_now"] == ["Architectural Spike"]
    assert second["read_now"] == ["Architectural Spike"]
    assert len(selected["read_now"]) == 3
    assert overflow["status"] == "reference_budget_exceeded"
