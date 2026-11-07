from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import MemorySaver

from archhypo_flow_agent.backend.app import create_app
from archhypo_flow_agent.graph import build_graph
from archhypo_flow_agent.graph.nodes.context_sufficiency import ContextSufficiency
from archhypo_flow_agent.services import AgentService
from tests.fakes import InMemoryArtifactRepository, StubSystemOneClient, stub_chat_model


def interview_model(reports):
    model = stub_chat_model()
    original = model.with_structured_output
    calls = []

    def structured(schema, **kwargs):
        if schema is ContextSufficiency:

            def respond(value):
                calls.append(value)
                return reports.pop(0)

            return RunnableLambda(respond)
        return original(schema, **kwargs)

    object.__setattr__(model, "with_structured_output", structured)
    return model, calls


def test_interview_resumes_and_keeps_questions_and_answers():
    model, calls = interview_model(
        [
            ContextSufficiency(status="needs_clarification", question="Which system?"),
            ContextSufficiency(status="needs_clarification", question="What concern?"),
            ContextSufficiency(
                status="sufficient", uncertainty="Can checkout handle peaks?"
            ),
        ]
    )
    router = StubSystemOneClient()
    graph = build_graph(
        model,
        system_one_client=router,
        artifact_repository=InMemoryArtifactRepository(),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "interview"}}
    first = graph.invoke(
        {"messages": [HumanMessage(content="I have a concern")]}, config
    )
    assert first["messages"][-1].content == "Which system?"
    assert first["interview_pending"]
    assert not first.get("hypothesis")

    second = graph.invoke({"messages": [HumanMessage(content="Checkout")]}, config)
    assert second["messages"][-1].content == "What concern?"
    assert router.calls == 1

    third = graph.invoke({"messages": [HumanMessage(content="Peak traffic")]}, config)
    assert not third["interview_pending"]
    assert third["hypothesis"]
    assert (
        graph.get_state(config).tasks[0].interrupts[0].value["kind"]
        == "hypothesis_review"
    )
    assert len(calls) == 3
    assert "Checkout" in str(calls[-1])


def test_disabled_hitl_skips_assessment_and_existing_pending_interview():
    model, calls = interview_model(
        [ContextSufficiency(status="needs_clarification", question="Which system?")]
    )
    graph = build_graph(
        model,
        system_one_client=StubSystemOneClient(),
        artifact_repository=InMemoryArtifactRepository(),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "disable-during-interview"}}
    graph.invoke({"messages": [HumanMessage(content="A concern")]}, config)
    result = graph.invoke(
        {"messages": [HumanMessage(content="I don't know")]},
        config,
        context={"global_context": "", "project_context": "", "hitl_enabled": False},
    )
    assert len(calls) == 1
    assert not result["interview_pending"]
    assert result["result"]
    assert not result.get("__interrupt__")


def test_stream_interview_survives_service_restart(tmp_path):
    database = tmp_path / "interview.sqlite"
    model, _ = interview_model([
        ContextSufficiency(status="needs_clarification", question="Which system?"),
    ])
    service = AgentService(
        model=model, system_one_client=StubSystemOneClient(), database_path=database
    )
    with TestClient(create_app(service)) as client:
        response = client.post(
            "/api/chat/stream", json={"thread_id": "interview", "message": "Concern"}
        )
        assert response.status_code == 200
        assert "Which system?" in response.text
    service.close()

    model, _ = interview_model([
        ContextSufficiency(
            status="sufficient", uncertainty="Can checkout handle peaks?"
        )
    ])
    router = StubSystemOneClient()
    service = AgentService(
        model=model, system_one_client=router, database_path=database
    )
    with TestClient(create_app(service)) as client:
        history = client.get("/api/threads/interview").json()
        assert history["messages"][-1]["content"] == "Which system?"
        response = client.post(
            "/api/chat/stream",
            json={"thread_id": "interview", "message": "Checkout peaks"},
        )
        assert response.status_code == 200
        assert "hypothesis_review" in response.text
        assert router.calls == 0
    service.close()
