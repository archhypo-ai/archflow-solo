"""Generate a Mermaid diagram from the compiled conversational graph."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from archhypo_flow_agent.graph import build_graph


class DiagramModel(FakeListChatModel):
    """Offline model stub used only while compiling the graph."""

    def __init__(self) -> None:
        super().__init__(responses=["diagram-only"], disable_streaming=True)

    def bind_tools(self, tools: Any, **kwargs: Any):
        """Allow graph construction without binding a real provider model."""

        return self


def generate_workflow_diagram(output_directory: Path) -> Path:
    """Write the compiled graph's Mermaid source into ``output_directory``."""

    output_directory.mkdir(parents=True, exist_ok=True)
    mermaid_path = output_directory / "archhypo-flow-agent.mmd"
    graph = build_graph(model=DiagramModel())
    diagram = graph.get_graph(xray=True).draw_mermaid()
    mermaid_path.write_text(diagram, encoding="utf-8")
    return mermaid_path


def main(arguments: Sequence[str] | None = None) -> None:
    """Run the workflow diagram command."""

    parser = argparse.ArgumentParser(
        description="Generate the ArchHypo Flow conversational graph as Mermaid."
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path.cwd() / "docs" / "architecture",
        help="Directory where the Mermaid file will be written.",
    )
    options = parser.parse_args(arguments)
    mermaid_path = generate_workflow_diagram(options.output_directory)
    print(f"Mermaid: {mermaid_path}")


if __name__ == "__main__":
    main()
