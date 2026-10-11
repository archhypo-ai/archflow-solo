"""Stateless, governed access to the ArchHypo catalog references."""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_REFERENCE_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*(?P<name>[^|]+?)\s*\|\s*"
    r"(?P<use_when>[^|]+?)\s*\|\s*(?P<related>[^|]*?)\s*\|\s*"
    r"`(?P<reference>[^`]+)`\s*\|\s*$"
)
_DEFAULT_MAX_CONTEXT_CHARS = 200_000
_MAX_REFERENCES_PER_REQUEST = 3
_CATALOG_ROOT = Path(__file__).resolve().parents[3] / "skills" / "archhypo-catalog"


class CatalogReadRequest(BaseModel):
    """Patterns requested by the Technical Planner Agent."""

    patterns: list[str] = Field(
        default_factory=list,
        max_length=_MAX_REFERENCES_PER_REQUEST,
        description=(
            "Exact pattern names from the catalog index. Request only the "
            "selected patterns."
        ),
    )


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Pattern metadata parsed from the skill index."""

    name: str
    use_when: str
    related_patterns: tuple[str, ...]
    reference: str


class CatalogReader:
    """Read catalog content without conversation or execution state."""

    def __init__(
        self,
        catalog_root: Path,
        *,
        max_context_chars: int = _DEFAULT_MAX_CONTEXT_CHARS,
    ) -> None:
        if max_context_chars <= 0:
            raise ValueError("max_context_chars must be positive")
        self.catalog_root = catalog_root
        self.max_context_chars = max_context_chars

    @property
    def index_path(self) -> Path:
        return self.catalog_root / "SKILL.md"

    def index(self) -> list[CatalogEntry]:
        """Parse pattern names and canonical paths from SKILL.md."""

        entries: list[CatalogEntry] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            match = _REFERENCE_ROW.match(line)
            if match is None:
                continue
            related = tuple(
                item.strip()
                for item in match.group("related").split(";")
                if item.strip() and item.strip() not in {"-", "—"}
            )
            entries.append(
                CatalogEntry(
                    name=match.group("name").strip(),
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
        unknown_related = sorted(
            {
                related
                for entry in entries
                for related in entry.related_patterns
                if related not in known_names
            }
        )
        if unknown_related:
            raise ValueError(
                "The catalog index contains unknown related pattern names: "
                + ", ".join(unknown_related)
            )
        return entries

    def read(self, *, patterns: Sequence[str] | None = None) -> dict[str, Any]:
        """Return the requested references for this call only.

        The reader deliberately has no run-, thread-, or process-session state.
        Conversation isolation belongs to LangGraph checkpoints; catalog reads
        are ordinary functional inputs and outputs.
        """

        entries = self.index()
        by_name = {entry.name: entry for entry in entries}
        requested = list(dict.fromkeys(patterns or []))
        if len(requested) > _MAX_REFERENCES_PER_REQUEST:
            return {
                "status": "error",
                "error": (
                    "A catalog read may request at most "
                    f"{_MAX_REFERENCES_PER_REQUEST} references."
                ),
                "max_references": _MAX_REFERENCES_PER_REQUEST,
                "requested": requested,
            }

        unknown = [name for name in requested if name not in by_name]
        if unknown:
            return {
                "status": "error",
                "error": "Unknown catalog pattern name(s).",
                "unknown": list(dict.fromkeys(unknown)),
                "available_patterns": list(by_name),
            }
        if not requested:
            return {
                "status": "error",
                "error": "Provide at least one catalog pattern name.",
                "available_patterns": list(by_name),
            }

        references: list[dict[str, Any]] = []
        chars_loaded = 0
        for name in requested:
            entry = by_name[name]
            path = self.catalog_root / entry.reference
            content = path.read_text(encoding="utf-8")
            if chars_loaded + len(content) > self.max_context_chars:
                return {
                    "status": "context_budget_exceeded",
                    "error": (
                        "The selected references exceed the catalog context "
                        f"budget of {self.max_context_chars} characters."
                    ),
                    "read_set": [item["pattern"] for item in references],
                    "read_now": [item["pattern"] for item in references],
                    "skipped_already_read": [],
                    "references": references,
                    "omitted": name,
                    "available_patterns": list(by_name),
                }

            chars_loaded += len(content)
            references.append(
                {
                    "pattern": name,
                    "path": f"/skills/archhypo-catalog/{entry.reference}",
                    "content": content,
                    "related_patterns": list(entry.related_patterns),
                }
            )

        return {
            "status": "ok",
            "mode": "selected",
            "read_set": requested,
            "read_now": requested,
            "skipped_already_read": [],
            "references": references,
            "available_patterns": list(by_name),
        }


@tool("read_archhypo_catalog", args_schema=CatalogReadRequest)
def read_archhypo_catalog(patterns: list[str] | None = None) -> dict[str, Any]:
    """Read selected ArchHypo references from the official catalog."""

    result = CatalogReader(_CATALOG_ROOT).read(patterns=patterns)
    logger.info(
        "catalog_read status=%s patterns=%s references=%s",
        result.get("status"),
        patterns or [],
        result.get("read_now", []),
    )
    return result


__all__ = [
    "CatalogEntry",
    "CatalogReadRequest",
    "CatalogReader",
    "read_archhypo_catalog",
]
