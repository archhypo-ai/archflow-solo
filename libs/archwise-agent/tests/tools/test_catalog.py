from pathlib import Path

from archwise_agent.tools.catalog import CatalogReader

CATALOG_ROOT = Path(__file__).resolve().parents[2] / "skills" / "archhypo-catalog"


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


def test_catalog_reader_isolates_runs_and_supports_complete_catalog_reads() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    first = reader.read(run_id="run-1", patterns=["Architectural Spike"])
    second = reader.read(run_id="run-2", patterns=["Architectural Spike"])
    all_patterns = reader.read(run_id="run-3", read_all=True)

    assert first["read_now"] == ["Architectural Spike"]
    assert second["read_now"] == ["Architectural Spike"]
    assert len(all_patterns["read_now"]) == 12
