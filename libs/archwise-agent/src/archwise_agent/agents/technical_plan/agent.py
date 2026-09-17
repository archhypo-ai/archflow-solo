"""Technical plan agent with progressive-disclosure skill support."""

from __future__ import annotations

from pathlib import Path

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware import FilesystemMiddleware, SkillsMiddleware
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models.chat_models import BaseChatModel

from archwise_agent.core import TechnicalPlan

PACKAGE_ROOT = Path(__file__).resolve().parents[4]

SYSTEM_PROMPT = """\
You are the ArchWise Technical Plan Agent.

Create a technical plan to reduce the architectural uncertainty represented by
the supplied hypothesis and classification.

Before selecting any pattern:
1. Load the `archhypo-catalog` skill using the available skill instructions.
2. Read the relevant pattern reference file from that skill.
3. Ground each selected pattern and its explanation in the reference you read.

Requirements:
- Generate between three and five concrete technical plan items.
- Each item must include a concise title, objective, description, one valid
  ArchHypo pattern, and an honest trade-off.
- Select patterns only from the official ArchHypo catalog.
- Make every action relevant to the specific hypothesis.
- Do not repeat the same action with different wording.
- Do not invent project facts, measurements, patterns, or evidence.
- Use the same language as the input.
"""


def build_technical_plan_agent(model: BaseChatModel):
    """Build a ReAct agent with filesystem-backed progressive skill loading."""

    backend = FilesystemBackend(root_dir=PACKAGE_ROOT, virtual_mode=True)
    return create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(TechnicalPlan),
        middleware=[
            FilesystemMiddleware(
                backend=backend,
                tools=["ls", "read_file", "glob"],
            ),
            SkillsMiddleware(
                backend=backend,
                sources=["/skills"],
            ),
        ],
        name="technical_plan_agent",
    )


__all__ = ["build_technical_plan_agent"]
