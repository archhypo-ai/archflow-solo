from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda

from archhypo_flow_agent.graph import workflow
from archhypo_flow_agent.tools import tavily_search
from tests.fakes import InMemoryArtifactRepository, StubSystemOneClient, stub_chat_model


def test_tavily_is_exposed_only_when_enabled_and_configured(monkeypatch):
    active = False
    monkeypatch.setattr(workflow, "is_available", lambda _: active)

    def agent(model, *, tools, **kwargs):
        text = "with-tool" if tools else "without-tool"
        return RunnableLambda(
            lambda data, **kwargs: {
                "messages": [*data["messages"], AIMessage(content=text)]
            }
        )

    monkeypatch.setattr(workflow, "build_direct_response_agent", agent)
    monkeypatch.setattr(workflow, "build_response_generation_agent", agent)
    graph = workflow.build_graph(
        stub_chat_model(),
        system_one_client=StubSystemOneClient(
            "contextual_question", "contextual_question"
        ),
        artifact_repository=InMemoryArtifactRepository(),
        tools=[tavily_search],
        dynamic_tavily=True,
    )
    assert (
        graph.invoke({"messages": [HumanMessage(content="Hello")]})["messages"][
            -1
        ].content
        == "without-tool"
    )
    active = True
    assert (
        graph.invoke({"messages": [HumanMessage(content="Hello")]})["messages"][
            -1
        ].content
        == "with-tool"
    )
