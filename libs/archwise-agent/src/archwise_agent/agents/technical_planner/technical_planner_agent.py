"""Technical planner agent with governed skill-catalog access."""

from __future__ import annotations

from pathlib import Path

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware import SkillsMiddleware
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models.chat_models import BaseChatModel

from archwise_agent.core import TechnicalPlan
from archwise_agent.tools import make_catalog_tool

PACKAGE_ROOT = Path(__file__).resolve().parents[4]
CATALOG_ROOT = PACKAGE_ROOT / "skills" / "archhypo-catalog"
CATALOG_INDEX = (CATALOG_ROOT / "SKILL.md").read_text(encoding="utf-8")

SKILLS_SYSTEM_PROMPT = """\
## ArchWise Skills

{skills_locations}{skills_load_warnings}

{skills_list}

The complete ArchHypo catalog index is included in the main instructions.
Use `read_archhypo_catalog` for references; do not use filesystem tools.
"""

SYSTEM_PROMPT = f"""\
You are the ArchWise Technical Planner Agent.

Create a technical plan to reduce the architectural uncertainty represented by
the supplied hypothesis and classification.

The complete official ArchHypo catalog index is included below. The final plan
must contain three to five items; this limit applies to the answer, not to the
research exploration.

Research protocol:
1. Screen the index and identify the primary patterns relevant to the
   uncertainty. Request up to five names with `read_archhypo_catalog`, or use
   `read_all=true` when comparing the complete catalog is justified.
2. Read the returned references and inspect their `Related Patterns` sections.
   A related pattern is only a one-hop suggestion. Request a new related
   catalog pattern only if it could change the plan.
3. The catalog reader keeps a read set per graph execution. It skips any
   pattern already loaded, so never try to force a reread of the same pattern.
4. Stop when the evidence is sufficient or the reader reports a context
   budget. Then select the three to five strongest patterns for the final plan.

Use only `read_archhypo_catalog` to access catalog references. Do not use
filesystem traversal, construct paths, follow relationships recursively, or
invent catalog patterns. The reader may load all patterns when `read_all=true`.

Requirements:
- Generate between three and five concrete technical plan items.
- Each item must include a concise title, objective, description, one valid
  ArchHypo pattern, and an honest trade-off.
- Select patterns only from the official ArchHypo catalog.
- Make every action relevant to the specific hypothesis.
- Do not repeat the same action with different wording.
- Do not invent project facts, measurements, patterns, or evidence.
- Use the same language as the input.

Authoritative catalog skill and index:
{CATALOG_INDEX}
"""


def build_technical_planner_agent(model: BaseChatModel):
    """Build the technical planner with one governed catalog tool."""

    backend = FilesystemBackend(root_dir=PACKAGE_ROOT, virtual_mode=True)
    catalog_tool = make_catalog_tool(CATALOG_ROOT)
    return create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[catalog_tool],
        response_format=ToolStrategy(TechnicalPlan),
        middleware=[
            SkillsMiddleware(
                backend=backend,
                sources=["/skills"],
                system_prompt=SKILLS_SYSTEM_PROMPT,
            )
        ],
        name="technical_planner_agent",
    )


__all__ = ["build_technical_planner_agent"]
