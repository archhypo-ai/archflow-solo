"""Generate a Mermaid diagram and PNG for the ArchWise workflow."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from archwise_agent import build_orchestrator_agent


class DiagramModel(FakeListChatModel):
    """Model stub used only to compile the graph without an LLM call."""

    def __init__(self) -> None:
        super().__init__(responses=["diagram-only"], disable_streaming=True)

    def with_structured_output(self, schema: Any, **kwargs: Any):
        """Provide a runnable so structured agents can be constructed."""

        return RunnableLambda(lambda _input: {})

    def bind_tools(self, tools: Any, **kwargs: Any):
        """Allow the technical-plan agent to be constructed."""

        return self


def generate_workflow_diagram(output_directory: Path) -> tuple[Path, Path]:
    """Generate the Mermaid source and PNG in ``output_directory``."""

    output_directory.mkdir(parents=True, exist_ok=True)
    mermaid_path = output_directory / "archwise-workflow.mmd"
    png_path = output_directory / "archwise-workflow.png"

    agent = build_orchestrator_agent(model=DiagramModel())
    graph = agent.get_graph()
    mermaid_path.write_text(graph.draw_mermaid(), encoding="utf-8")
    png_path.write_bytes(graph.draw_mermaid_png())
    return mermaid_path, png_path


def main(arguments: Sequence[str] | None = None) -> None:
    """Run the workflow diagram generator command."""

    parser = argparse.ArgumentParser(
        description="Generate the ArchWise workflow Mermaid diagram and PNG."
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path.cwd() / "docs" / "architecture",
        help="Directory where the Mermaid and PNG files will be written.",
    )
    options = parser.parse_args(arguments)
    mermaid_path, png_path = generate_workflow_diagram(options.output_directory)
    print(f"Mermaid: {mermaid_path}")
    print(f"PNG: {png_path}")


if __name__ == "__main__":
    main()
