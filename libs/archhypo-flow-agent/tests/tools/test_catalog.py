from pathlib import Path

import pytest
from pydantic import ValidationError

from archhypo_flow_agent.core import CatalogPatternSelection
from archhypo_flow_agent.tools.catalog import CatalogReader, render_references

CATALOG_ROOT = Path(__file__).resolve().parents[2] / "skills" / "archhypo-catalog"


def test_catalog_index_has_the_twelve_canonical_patterns() -> None:
    reader = CatalogReader(CATALOG_ROOT)
    entries = {entry.name: entry for entry in reader.index()}

    assert len(entries) == 12
    assert entries["Architectural Spike"].related_patterns == (
        "Bring the Specialist",
        "Technical Debt Management",
        "Tracer Bullets",
    )
    assert "# ArchHypo Catalog" in reader.skill_index()


def test_catalog_reader_loads_only_the_selected_references() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    references = reader.read(
        ["Architectural Spike", "Postpone Uncertain Decisions"]
    )
    rendered = render_references(references)

    assert [reference.pattern for reference in references] == [
        "Architectural Spike",
        "Postpone Uncertain Decisions",
    ]
    assert all(reference.content.startswith("# ") for reference in references)
    assert "## Architectural Spike" in rendered
    assert "## Postpone Uncertain Decisions" in rendered
    assert "## Continuous Inspection" not in rendered


def test_all_catalog_markdown_references_are_readable_in_batches_of_three() -> None:
    reader = CatalogReader(CATALOG_ROOT)
    pattern_names = [entry.name for entry in reader.index()]

    loaded = []
    for offset in range(0, len(pattern_names), 3):
        loaded.extend(reader.read(pattern_names[offset : offset + 3]))

    assert len(loaded) == 12
    assert all(reference.content.strip() for reference in loaded)


def test_catalog_reader_enforces_the_three_reference_limit() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    with pytest.raises(ValueError, match="at most 3"):
        reader.read(
            [
                "Architectural Spike",
                "Quality Checkpoint",
                "Technical Debt Management",
                "Tracer Bullets",
            ]
        )


def test_catalog_reader_rejects_unknown_patterns() -> None:
    reader = CatalogReader(CATALOG_ROOT)

    with pytest.raises(ValueError, match="Unknown ArchHypo catalog pattern"):
        reader.read(["Unknown pattern"])


def test_catalog_selection_limits_candidates_and_selected_references() -> None:
    selection = CatalogPatternSelection(
        candidate_patterns=[
            "Architectural Spike",
            "Tracer Bullets",
            "Bring the Specialist",
            "Learning from Experiments",
            "Quality Checkpoint",
        ],
        selected_patterns=[
            "Architectural Spike",
            "Tracer Bullets",
            "Quality Checkpoint",
        ],
        rationale="These patterns can collect evidence and set a decision checkpoint.",
    )

    assert len(selection.candidate_patterns) == 5
    assert len(selection.selected_patterns) == 3

    with pytest.raises(ValidationError, match="selected patterns must come"):
        CatalogPatternSelection(
            candidate_patterns=["Architectural Spike"],
            selected_patterns=["Tracer Bullets"],
            rationale="The selected pattern was not screened as a candidate.",
        )

    with pytest.raises(ValidationError):
        CatalogPatternSelection(
            candidate_patterns=[
                "Architectural Spike",
                "Tracer Bullets",
                "Bring the Specialist",
                "Learning from Experiments",
                "Quality Checkpoint",
                "Technical Debt Management",
            ],
            selected_patterns=["Architectural Spike"],
            rationale="The candidate list exceeds the screening limit.",
        )
