"""Generate a Mermaid diagram from the compiled conversational graph."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from archhypo_flow_agent.graph import build_graph
from archhypo_flow_agent.providers import SystemOneResponse


class DiagramModel(FakeListChatModel):
    """Offline model stub used only while compiling the graph."""

    def __init__(self) -> None:
        super().__init__(responses=["diagram-only"], disable_streaming=True)

    def bind_tools(self, tools: Any, **kwargs: Any):
        """Allow graph construction without binding a real provider model."""

        return self

    def with_structured_output(self, schema: Any, **kwargs: Any):
        """Allow structured agent construction without an LLM call."""

        return RunnableLambda(lambda _input: schema.model_construct())


class DiagramSystemOneClient:
    """Offline dependency used only to compile, never execute, the diagram."""

    def decide(
        self,
        *,
        state: str | dict[str, Any] | list[Any],
        questions: Mapping[str, Mapping[str, Any]],
        session_id: str | None = None,
    ) -> SystemOneResponse:
        raise RuntimeError("Diagram generation must not request SystemOne decisions")


class DiagramArtifactRepository:
    """Offline dependency used only to compile, never execute, the diagram."""

    def save_final_result(self, **_kwargs: object) -> str:
        raise RuntimeError("Diagram generation must not persist artifacts")


def generate_workflow_diagram(output_directory: Path) -> tuple[Path, Path]:
    """Write the compiled graph's Mermaid source and PNG to ``output_directory``."""

    output_directory.mkdir(parents=True, exist_ok=True)
    mermaid_path = output_directory / "archhypo-flow-agent.mmd"
    png_path = output_directory / "archhypo-flow-agent.png"
    graph = build_graph(
        model=DiagramModel(),
        system_one_client=DiagramSystemOneClient(),
        artifact_repository=DiagramArtifactRepository(),
        chat_model_id="diagram-only",
        system_one_model_id="diagram-only",
    )
    drawable_graph = graph.get_graph(xray=True)
    mermaid_path.write_text(drawable_graph.draw_mermaid(), encoding="utf-8")
    png_path.write_bytes(drawable_graph.draw_mermaid_png())
    return mermaid_path, png_path


def main(arguments: Sequence[str] | None = None) -> None:
    """Run the workflow diagram command."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate the ArchHypo Flow conversational graph as Mermaid and PNG."
        )
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
