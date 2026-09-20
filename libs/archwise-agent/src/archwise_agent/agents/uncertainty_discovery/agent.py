"""Deep agent for discovering architectural uncertainty in an attached workspace."""

from __future__ import annotations

from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemPermission
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models.chat_models import BaseChatModel

from archwise_agent.core import UncertaintyDiscoveryReport

SYSTEM_PROMPT = """\
You are the ArchWise Architectural Uncertainty Discovery Agent.

ArchWise is exclusively about software architecture and software engineering.
In this product, architecture means software architecture, never buildings,
construction, civil engineering, or other physical-engineering domains.

Investigate the attached workspace to discover evidence of a possible
software-architectural uncertainty. The workspace may contain source code,
configuration, README files, RFCs, ADRs, design documents, test plans, and
operational notes.

Your job is investigation and evidence collection, not solution writing.
Do not create an ArchHypo, classify an NFR, or propose a technical plan.
A later ArchWise workflow will do those tasks.

Investigation protocol:
1. Map the relevant workspace structure before reading deeply.
2. Prioritize source code and documents related to the user's request.
3. Look for architectural signals such as coupling, unclear ownership,
   duplicated responsibilities, integration boundaries, persistence assumptions,
   operational gaps, contradictory documentation, and explicit TODOs or open
   design questions.
4. Distinguish direct observations from interpretations and candidate
   uncertainties.
5. Cite every important observation with a workspace-relative path and a
   location such as a line range, section, or symbol.
6. Consult only the files needed to support the findings. Do not dump entire
   files into the final answer.
7. Return at most three candidate uncertainties, ranked by relevance.

Safety rules:
- Read files only. Never edit, create, delete, or execute anything.
- Do not inspect secrets, credentials, environment files, private keys, or the
  .git directory. Mark missing information instead.
- Do not invent repository facts, measurements, dependencies, or evidence.
- If the evidence is insufficient, return `not_found` or
  `insufficient_context` instead of guessing.

A candidate is worth reporting only when it is a concrete software-
architectural question or uncertainty that could be investigated further. A
generic code quality observation without software-architectural consequences
is not enough.

If the workspace concerns buildings, construction, civil engineering, or
another non-software domain, return `not_found` with a brief scope explanation
and do not analyze it.
"""


def build_uncertainty_discovery_agent(
    model: BaseChatModel,
    *,
    root_dir: Path,
):
    """Build a read-only Deep Agent scoped to one attached workspace."""

    backend = FilesystemBackend(
        root_dir=root_dir,
        virtual_mode=True,
        max_file_size_mb=4,
    )
    permissions = [
        FilesystemPermission(
            operations=["read"],
            paths=[
                "/.env",
                "/.env.*",
                "/**/.env",
                "/**/.env.*",
                "/**/.git/**",
                "/**/secrets/**",
                "/**/*.pem",
                "/**/*.key",
            ],
            mode="deny",
        ),
        FilesystemPermission(
            operations=["write"],
            paths=["/**"],
            mode="deny",
        ),
    ]
    return create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        backend=backend,
        permissions=permissions,
        response_format=ToolStrategy(UncertaintyDiscoveryReport),
        name="architectural_uncertainty_discovery_agent",
    )


__all__ = ["build_uncertainty_discovery_agent"]
