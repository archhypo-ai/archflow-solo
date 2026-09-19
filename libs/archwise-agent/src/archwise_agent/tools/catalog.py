"""Governed access to the ArchHypo catalog references."""

from __future__ import annotations

import logging
import re
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any

from langchain.tools import ToolRuntime
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_REFERENCE_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*(?P<name>[^|]+?)\s*\|\s*"
    r"(?P<use_when>[^|]+?)\s*\|\s*`(?P<reference>[^`]+)`\s*\|\s*$"
)
_DEFAULT_MAX_CONTEXT_CHARS = 200_000
_MAX_SESSIONS = 128


class CatalogReadRequest(BaseModel):
    """Patterns requested by the Technical Planner Agent."""

    patterns: list[str] = Field(
        default_factory=list,
        max_length=100,
        description=(
            "Exact pattern names from the catalog index. Use this for selected "
            "primary or one-hop related patterns."
        ),
    )
    read_all: bool = Field(
        default=False,
        description=(
            "Read every pattern in the catalog when comparing the complete "
            "catalog is justified. The final answer still contains only 3–5 items."
        ),
    )


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Pattern metadata parsed from the skill index."""

    name: str
    use_when: str
    reference: str


@dataclass(slots=True)
class _ReadSession:
    read_set: set[str] = field(default_factory=set)
    chars_loaded: int = 0


class CatalogReader:
    """Read catalog content with per-run deduplication and context budgeting."""

    def __init__(
        self,
        catalog_root: Path,
        *,
        max_context_chars: int = _DEFAULT_MAX_CONTEXT_CHARS,
        max_sessions: int = _MAX_SESSIONS,
    ) -> None:
        if max_context_chars <= 0:
            raise ValueError("max_context_chars must be positive")
        if max_sessions <= 0:
            raise ValueError("max_sessions must be positive")
        self.catalog_root = catalog_root
        self.max_context_chars = max_context_chars
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[str, _ReadSession] = OrderedDict()
        self._lock = RLock()

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
            entries.append(
                CatalogEntry(
                    name=match.group("name").strip(),
                    use_when=match.group("use_when").strip(),
                    reference=match.group("reference").strip(),
                )
            )
        if not entries:
            raise ValueError("The catalog index contains no patterns")
        names = [entry.name for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError("The catalog index contains duplicate pattern names")
        return entries

    def read(
        self,
        *,
        run_id: str,
        patterns: Sequence[str] | None = None,
        read_all: bool = False,
    ) -> dict[str, Any]:
        """Return newly requested references and skip files already in context."""

        entries = self.index()
        by_name = {entry.name: entry for entry in entries}
        requested = list(by_name) if read_all else list(patterns or [])
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
                "error": "Provide patterns or set read_all=true.",
                "available_patterns": list(by_name),
            }

        with self._lock:
            session = self._session_for(run_id)
            references: list[dict[str, str]] = []
            skipped: list[str] = []
            for name in dict.fromkeys(requested):
                if name in session.read_set:
                    skipped.append(name)
                    continue

                entry = by_name[name]
                path = self.catalog_root / entry.reference
                content = path.read_text(encoding="utf-8")
                if session.chars_loaded + len(content) > self.max_context_chars:
                    return {
                        "status": "context_budget_exceeded",
                        "error": (
                            "The selected references exceed the catalog context "
                            f"budget of {self.max_context_chars} characters."
                        ),
                        "read_set": sorted(session.read_set),
                        "read_now": [item["pattern"] for item in references],
                        "skipped_already_read": skipped,
                        "references": references,
                        "omitted": name,
                        "available_patterns": list(by_name),
                    }

                session.read_set.add(name)
                session.chars_loaded += len(content)
                references.append(
                    {
                        "pattern": name,
                        "path": f"/skills/archhypo-catalog/{entry.reference}",
                        "content": content,
                    }
                )

            return {
                "status": "ok",
                "mode": "all" if read_all else "selected",
                "read_set": sorted(session.read_set),
                "read_now": [item["pattern"] for item in references],
                "skipped_already_read": skipped,
                "references": references,
                "available_patterns": list(by_name),
            }

    def _session_for(self, run_id: str) -> _ReadSession:
        session = self._sessions.pop(run_id, None)
        if session is None:
            if len(self._sessions) >= self.max_sessions:
                self._sessions.popitem(last=False)
            session = _ReadSession()
        self._sessions[run_id] = session
        return session


def _runtime_run_id(runtime: ToolRuntime | None) -> str:
    if runtime is None:
        return "standalone"
    context = runtime.context
    if isinstance(context, dict) and context.get("run_id"):
        return str(context["run_id"])
    configurable = runtime.config.get("configurable", {})
    if isinstance(configurable, dict):
        if configurable.get("run_id"):
            return str(configurable["run_id"])
        if configurable.get("thread_id"):
            return str(configurable["thread_id"])
    return "standalone"


def make_catalog_tool(
    catalog_root: Path,
    *,
    max_context_chars: int = _DEFAULT_MAX_CONTEXT_CHARS,
):
    """Create the only catalog access tool for one technical-plan agent."""

    reader = CatalogReader(
        catalog_root,
        max_context_chars=max_context_chars,
    )

    @tool("read_archhypo_catalog", args_schema=CatalogReadRequest)
    def read_archhypo_catalog(
        patterns: list[str] | None = None,
        read_all: bool = False,
        runtime: ToolRuntime | None = None,
    ) -> dict[str, Any]:
        """Read selected ArchHypo references without filesystem traversal.

        Pattern names are resolved from the skill's SKILL.md index. The reader
        owns a read set per graph run, so related-pattern requests cannot reread
        content already supplied to the model.
        """

        result = reader.read(
            run_id=_runtime_run_id(runtime),
            patterns=patterns,
            read_all=read_all,
        )
        logger.info(
            "catalog_read status=%s mode=%s read_now=%s skipped=%s read_set=%s",
            result.get("status"),
            result.get("mode", "-"),
            result.get("read_now", []),
            result.get("skipped_already_read", []),
            result.get("read_set", []),
        )
        return result

    return read_archhypo_catalog


__all__ = [
    "CatalogEntry",
    "CatalogReadRequest",
    "CatalogReader",
    "make_catalog_tool",
]
