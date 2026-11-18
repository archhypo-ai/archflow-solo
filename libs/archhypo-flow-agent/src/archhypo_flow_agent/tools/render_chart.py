"""Return validated chart data for the desktop's native CopilotKit renderer."""

import json
import math
from typing import Literal

from langchain_core.tools import tool


@tool
def render_chart(
    title: str,
    chart_type: Literal["bar", "line", "pie"],
    data: list[dict[str, object]],
) -> str:
    """Render a chart from labeled numeric values.

    Use only values supplied by the user or present in the conversation. Do not
    invent data. Each data item must contain a string label and numeric value.
    """
    if not title.strip():
        return json.dumps({"error": "Chart title cannot be empty."})
    if not 1 <= len(data) <= 24:
        return json.dumps({"error": "A chart must contain between 1 and 24 values."})

    points: list[dict[str, str | int | float]] = []
    for item in data:
        label = item.get("label")
        value = item.get("value")
        if not isinstance(label, str) or not label.strip():
            return json.dumps({"error": "Each chart value requires a non-empty label."})
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            return json.dumps({"error": "Each chart value must be numeric."})
        if chart_type == "pie" and value < 0:
            return json.dumps({"error": "Pie chart values cannot be negative."})
        points.append({"label": label[:80], "value": value})

    return json.dumps(
        {"title": title[:120], "chart_type": chart_type, "data": points},
        ensure_ascii=False,
    )


__all__ = ["render_chart"]
