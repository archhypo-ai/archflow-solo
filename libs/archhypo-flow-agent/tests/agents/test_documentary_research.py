from archhypo_flow_agent.agents import documentary_research
from archhypo_flow_agent.services.document_extraction import ExtractedDocument


def test_document_tools_access_only_the_supplied_snapshot(monkeypatch):
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(documentary_research, "create_deep_agent", capture)
    documentary_research.build_documentary_research_agent(
        object(), [ExtractedDocument(name="adr.md", text="Decision\nContext")]
    )
    tools = {tool.name: tool for tool in captured["tools"]}
    assert tools["list_documents"].invoke({}) == "0: adr.md"
    assert "2: Context" in tools["read_document"].invoke(
        {"document_id": 0, "start_line": 2, "line_count": 1}
    )
    assert "Unknown" in tools["read_document"].invoke({"document_id": -1})
    assert "Unknown" in tools["read_document"].invoke({"document_id": 1})
    assert "between 1 and 100" in tools["read_document"].invoke(
        {"document_id": 0, "line_count": 101}
    )


def test_document_read_budget_is_bounded(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        documentary_research,
        "create_deep_agent",
        lambda **kwargs: captured.update(kwargs),
    )
    documentary_research.build_documentary_research_agent(
        object(), [ExtractedDocument(name="adr.md", text="Decision")]
    )
    reader = next(tool for tool in captured["tools"] if tool.name == "read_document")
    for _ in range(20):
        assert "Decision" in reader.invoke({"document_id": 0})
    assert "limit reached" in reader.invoke({"document_id": 0})


def test_long_line_is_not_truncated(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        documentary_research,
        "create_deep_agent",
        lambda **kwargs: captured.update(kwargs),
    )
    text = "a" * 15_000 + " end"
    documentary_research.build_documentary_research_agent(
        object(), [ExtractedDocument(name="adr.md", text=text)]
    )
    reader = next(tool for tool in captured["tools"] if tool.name == "read_document")
    assert reader.invoke({"document_id": 0, "line_count": 1}).endswith(text)
