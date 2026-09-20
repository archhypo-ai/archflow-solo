"""Deterministic rendering node for ArchWise results."""

from __future__ import annotations

from langgraph.runtime import Runtime

from archwise_agent.core import ArchHypo, ArchHypoState, RunContext
from archwise_agent.graph import GraphNode, raise_if_cancelled


def create_archwise_result_rendering_node() -> GraphNode[
    ArchHypoState, RunContext
]:
    """Create the deterministic fallback renderer for a completed result."""

    def render(
        state: ArchHypoState,
        runtime: Runtime[RunContext] | None = None,
    ) -> dict[str, object]:
        raise_if_cancelled(runtime)
        raw_result = state.get("result")
        if raw_result is None:
            raise ValueError("ArchWise result is required before rendering")
        result = (
            raw_result
            if isinstance(raw_result, ArchHypo)
            else ArchHypo.model_validate(raw_result)
        )
        response = render_archhypo_response(result)
        raise_if_cancelled(runtime)
        return {"response": response}

    return render


def render_archhypo_response(result: ArchHypo) -> str:
    """Render an ArchHypo result without another model call."""

    classification = result.classification
    nfr_justification = _table_cell(classification.nfr_justification)
    impact_justification = _table_cell(classification.impact_justification)
    uncertainty_justification = _table_cell(
        classification.uncertainty_justification
    )
    lines = [
        "## ArchWise analysis",
        "",
        "### Central uncertainty",
        "",
        result.uncertainty,
        "",
        "### Hypothesis",
        "",
        f"**{result.hypothesis.title}**",
        "",
        result.hypothesis.statement,
        "",
        f"**Justification:** {result.hypothesis.justification}",
        "",
        "### Classification",
        "",
        "| Attribute | Value | Justification |",
        "|---|---|---|",
        f"| NFR | {classification.nfr} | {nfr_justification} |",
        f"| Impact | {classification.impact} | {impact_justification} |",
        f"| Uncertainty | {classification.uncertainty} | "
        f"{uncertainty_justification} |",
        "",
        "### Technical plan",
        "",
    ]

    for index, item in enumerate(result.technical_plan.items, start=1):
        lines.extend(
            [
                f"{index}. **{item.title}** — `{item.pattern}`",
                "",
                f"**Objective:** {item.objective}",
                "",
                item.description,
                "",
                f"**Trade-off:** {item.tradeoff}",
                "",
            ]
        )

    discovery = result.discovery
    if discovery is not None and discovery.evidence:
        lines.extend(["### Workspace evidence", ""])
        for evidence in discovery.evidence:
            location = _table_cell(evidence.location)
            observation = _table_cell(evidence.observation)
            path = evidence.path.replace("`", "'")
            lines.append(
                f"- `{path}` ({location}) — {observation}"
            )
        lines.append("")

    lines.extend(
        [
            "### Rationale",
            "",
            result.technical_plan.rationale,
        ]
    )
    return "\n".join(lines)


def _table_cell(value: str) -> str:
    """Keep generated Markdown tables structurally valid."""

    return value.replace("|", r"\|").replace("\n", " ").strip()


__all__ = [
    "create_archwise_result_rendering_node",
    "render_archhypo_response",
]
