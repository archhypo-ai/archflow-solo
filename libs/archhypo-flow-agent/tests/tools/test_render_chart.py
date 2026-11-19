import json

from archhypo_flow_agent.tools.render_chart import render_chart


def test_chart_tool_returns_chart_payload():
    result = render_chart.invoke({
        "title": "Requests by service",
        "chart_type": "bar",
        "data": [
            {"label": "API", "value": 12},
            {"label": "Worker", "value": 7},
        ],
    })

    assert json.loads(result) == {
        "title": "Requests by service",
        "chart_type": "bar",
        "data": [
            {"label": "API", "value": 12},
            {"label": "Worker", "value": 7},
        ],
    }


def test_pie_chart_rejects_negative_values():
    result = render_chart.invoke({
        "title": "Distribution",
        "chart_type": "pie",
        "data": [{"label": "A", "value": -1}],
    })

    assert "cannot be negative" in json.loads(result)["error"]


def test_chart_tool_rejects_empty_data():
    result = render_chart.invoke({
        "title": "Empty",
        "chart_type": "line",
        "data": [],
    })

    assert "between 1 and 24" in json.loads(result)["error"]
