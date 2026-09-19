"""Technical planner agent with governed skill-catalog access."""

from __future__ import annotations

from pathlib import Path

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware import SkillsMiddleware
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models.chat_models import BaseChatModel

from archwise_agent.core import TechnicalPlan
from archwise_agent.tools import read_archhypo_catalog

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
must contain one to three items; this limit applies to the answer, not to the
research exploration.

Research protocol:
1. Screen the complete catalog index and classify up to five candidates.
2. Select up to three strongest patterns using their summaries and related
   official patterns. Do not read a reference merely to create a candidate.
3. Make one call to `read_archhypo_catalog` with only the selected patterns.
   The request may contain at most three references.
4. Use the returned references to create a concise plan. Do not call the tool
   again, request additional related references, or traverse relationships
   recursively.

Use only `read_archhypo_catalog` to access catalog references. Do not use
filesystem traversal, construct paths, follow relationships recursively, or
invent catalog patterns. The tool is stateless: its output is scoped to the
current call, so do not infer or request an "already read" session.

Requirements:
- Generate between one and three concrete technical plan items.
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
    return create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[read_archhypo_catalog],
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
