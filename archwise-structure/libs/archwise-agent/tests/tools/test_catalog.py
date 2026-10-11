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


def test_catalog_reader_is_stateless_between_calls() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    first = reader.read(patterns=["Architectural Spike"])
    second = reader.read(patterns=["Architectural Spike"])

    assert first["read_now"] == ["Architectural Spike"]
    assert second["read_now"] == ["Architectural Spike"]
    assert first["references"] == second["references"]
    assert first["skipped_already_read"] == []
    assert second["skipped_already_read"] == []


def test_catalog_reader_enforces_request_budget() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    selected = reader.read(
        patterns=[
            "Architectural Spike",
            "Quality Checkpoint",
            "Technical Debt Management",
        ]
    )
    overflow = reader.read(
        patterns=[
            "Continuous Inspection",
            "Learning from Experiments",
            "Plan for Preparation",
            "Tracer Bullets",
        ]
    )

    assert len(selected["read_now"]) == 3
    assert overflow["status"] == "error"
    assert overflow["max_references"] == 3
