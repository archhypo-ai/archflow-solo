"""Bounded, read-only access to the governed ArchHypo pattern catalog."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast, get_args

from archhypo_flow_agent.core import ArchHypoPattern

_INDEX_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*(?P<name>[^|]+?)\s*\|\s*"
    r"(?P<use_when>[^|]+?)\s*\|\s*(?P<related>[^|]*?)\s*\|\s*"
    r"`(?P<reference>[^`]+)`\s*\|\s*$"
)
_MAX_REFERENCES = 3
_DEFAULT_MAX_REFERENCE_CHARS = 200_000
_PATTERN_NAMES = set(get_args(ArchHypoPattern))
_PACKAGE_CATALOG_ROOT = (
    Path(__file__).resolve().parents[1] / "skills" / "archhypo-catalog"
)
_SOURCE_CATALOG_ROOT = (
    Path(__file__).resolve().parents[3] / "skills" / "archhypo-catalog"
)
_CATALOG_ROOT = (
    _PACKAGE_CATALOG_ROOT
    if _PACKAGE_CATALOG_ROOT.is_dir()
    else _SOURCE_CATALOG_ROOT
)


def _as_pattern(value: str) -> ArchHypoPattern:
    if value not in _PATTERN_NAMES:
        raise ValueError(f"Unknown ArchHypo catalog pattern: {value}")
    return cast(ArchHypoPattern, value)


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Metadata for one official pattern in the skill index."""

    name: ArchHypoPattern
    use_when: str
    related_patterns: tuple[ArchHypoPattern, ...]
    reference: str


@dataclass(frozen=True, slots=True)
class CatalogReference:
    """One selected Markdown source loaded for technical planning."""

    pattern: ArchHypoPattern
    path: str
    content: str
    related_patterns: tuple[ArchHypoPattern, ...]


class CatalogReader:
    """Read the skill index and at most three selected pattern references."""

    def __init__(
        self,
        catalog_root: Path = _CATALOG_ROOT,
        *,
        max_reference_chars: int = _DEFAULT_MAX_REFERENCE_CHARS,
    ) -> None:
        if max_reference_chars <= 0:
            raise ValueError("max_reference_chars must be positive")
        self.catalog_root = catalog_root
        self.max_reference_chars = max_reference_chars

    @property
    def skill_path(self) -> Path:
        return self.catalog_root / "SKILL.md"

    def skill_index(self) -> str:
        """Return the full catalog skill after validating its pattern table."""

        content = self.skill_path.read_text(encoding="utf-8")
        self.index(content=content)
        return content

    def index(self, *, content: str | None = None) -> list[CatalogEntry]:
        """Parse and validate the catalog's canonical names and references."""

        index_content = (
            content
            if content is not None
            else self.skill_path.read_text(encoding="utf-8")
        )
        entries: list[CatalogEntry] = []
        for line in index_content.splitlines():
            match = _INDEX_ROW.match(line)
            if match is None:
                continue
            try:
                name = _as_pattern(match.group("name").strip())
                related = tuple(
                    _as_pattern(value.strip())
                    for value in match.group("related").split(";")
                    if value.strip() and value.strip() not in {"-", "—"}
                )
            except ValueError as error:
                raise ValueError(
                    "The catalog index contains an unknown pattern"
                ) from error
            entries.append(
                CatalogEntry(
                    name=name,
                    use_when=match.group("use_when").strip(),
                    related_patterns=related,
                    reference=match.group("reference").strip(),
                )
            )

        if not entries:
            raise ValueError("The catalog index contains no patterns")
        names = [entry.name for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError("The catalog index contains duplicate pattern names")
        known_names = set(names)
        unknown_related = {
            related
            for entry in entries
            for related in entry.related_patterns
            if related not in known_names
        }
        if unknown_related:
            raise ValueError(
                "The catalog index contains unknown related patterns: "
                + ", ".join(sorted(unknown_related))
            )
        return entries

    def read(
        self,
        patterns: Sequence[ArchHypoPattern | str],
    ) -> tuple[CatalogReference, ...]:
        """Load only requested references, enforcing catalog and size bounds."""

        requested = list(patterns)
        if not requested:
            raise ValueError("Select at least one ArchHypo catalog pattern")
        if len(requested) > _MAX_REFERENCES:
            raise ValueError(
                f"A catalog read may request at most {_MAX_REFERENCES} references"
            )
        if len(requested) != len(set(requested)):
            raise ValueError("A catalog read cannot contain duplicate patterns")

        entries = {entry.name: entry for entry in self.index()}
        references: list[CatalogReference] = []
        total_chars = 0
        root = self.catalog_root.resolve()
        for requested_name in requested:
            try:
                name = _as_pattern(requested_name)
            except ValueError as error:
                raise ValueError(
                    f"Unknown ArchHypo catalog pattern: {requested_name}"
                ) from error
            entry = entries.get(name)
            if entry is None:
                raise ValueError(f"Pattern is missing from the catalog: {name}")

            relative_path = Path(entry.reference)
            if (
                relative_path.is_absolute()
                or relative_path.suffix != ".md"
                or not relative_path.parts
                or relative_path.parts[0] != "references"
            ):
                raise ValueError(f"Invalid catalog reference path for {name}")
            path = (root / relative_path).resolve()
            if not path.is_relative_to(root):
                raise ValueError(f"Catalog reference escapes the catalog root: {name}")
            content = path.read_text(encoding="utf-8")
            total_chars += len(content)
            if total_chars > self.max_reference_chars:
                raise ValueError(
                    "Selected catalog references exceed the configured context budget"
                )
            references.append(
                CatalogReference(
                    pattern=name,
                    path=f"/skills/archhypo-catalog/{relative_path.as_posix()}",
                    content=content,
                    related_patterns=entry.related_patterns,
                )
            )
        return tuple(references)


def render_references(references: Sequence[CatalogReference]) -> str:
    """Format selected sources for the technical-planning prompt."""

    sections = []
    for reference in references:
        related = ", ".join(reference.related_patterns) or "None"
        sections.append(
            f"## {reference.pattern}\n"
            f"Catalog path: {reference.path}\n"
            f"Related official patterns: {related}\n\n{reference.content}"
        )
    return "\n\n---\n\n".join(sections)


__all__ = [
    "CatalogEntry",
    "CatalogReader",
    "CatalogReference",
    "render_references",
]
