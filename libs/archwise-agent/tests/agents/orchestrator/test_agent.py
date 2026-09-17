import threading
import time

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService, Hypothesis, build_archwise_agent
from archwise_agent.core import AgentCancelledError
from tests.fakes import fake_hypothesis_model


def test_request_router_answers_direct_questions_without_archhypo() -> None:
    service = AgentService(
        model=fake_hypothesis_model(
            ["unused"],
            route="direct_response",
            direct_response="Tirana.",
        ),
        checkpointer=InMemorySaver(),
    )

    turn = service.send(
        thread_id="direct-thread",
        message="What is the capital of Albania?",
    )

    assert turn.result is None
    assert turn.text == "Tirana."
    conversation = service.get_conversation("direct-thread")
    assert conversation is not None
    assert conversation.messages[-1].content == "Tirana."


def test_agent_runs_one_uncertainty_at_a_time() -> None:
    model = fake_hypothesis_model(["first reply", "second reply"])
    agent = AgentService(model=model, checkpointer=InMemorySaver())

    first = agent.send(thread_id="thread-1", message="hello")
    second = agent.send(thread_id="thread-1", message="follow up")

    assert first.result.hypothesis == Hypothesis(
        uncertainty="hello",
        title="Hypothesis 1",
        statement="first reply",
        justification="Derived from the supplied uncertainty.",
    )
    assert first.text == "ArchWise response."
    assert second.text == "ArchWise response."

    state = agent.agent.get_state({"configurable": {"thread_id": "thread-1"}})
    assert state.values["uncertainty"] == "follow up"
    assert state.values["result"].hypothesis.statement == "second reply"
    assert len(state.values["messages"]) == 10
    assert [message.name for message in state.values["messages"][-4:]] == [
        "hypothesis_agent",
        "classifier_agent",
        "technical_plan_agent",
        "response_agent",
    ]


def test_agent_stream_can_be_cancelled() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["a" * 40], sleep=0.2),
        checkpointer=InMemorySaver(),
    )
    stream = service.stream(
        thread_id="cancel-thread",
        message="hello",
        run_id="cancel-run",
    )
    assert next(stream).type == "phase"

    events = []
    consumer = threading.Thread(target=lambda: events.extend(stream))
    consumer.start()
    time.sleep(0.05)

    assert service.cancel_run("cancel-run") is True
    consumer.join(timeout=3)

    assert not consumer.is_alive()
    assert any(event.type == "cancelled" for event in events)
    assert not any(event.type == "done" for event in events)


def test_deleting_an_active_run_cancels_it_and_removes_the_thread() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["reply"], sleep=0.2),
        checkpointer=InMemorySaver(),
    )
    errors: list[Exception] = []

    def run() -> None:
        try:
            service.send(
                thread_id="delete-thread",
                message="delete this",
                run_id="delete-run",
            )
        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=run)
    worker.start()
    time.sleep(0.05)

    assert service.delete_conversation("delete-thread") is True
    assert service.get_conversation("delete-thread") is None
    assert service.list_conversations() == []
    worker.join(timeout=3)

    assert not worker.is_alive()
    assert errors and isinstance(errors[0], AgentCancelledError)
    assert service.get_conversation("delete-thread") is None
    assert service.cancel_run("delete-run") is False


def test_cancelling_an_active_run_does_not_persist_its_response() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["reply"], sleep=0.2),
        checkpointer=InMemorySaver(),
    )
    errors: list[Exception] = []

    def run() -> None:
        try:
            service.send(
                thread_id="cancel-thread",
                message="stop this",
                run_id="cancel-run",
            )
        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=run)
    worker.start()
    time.sleep(0.05)

    assert service.cancel_run("cancel-run") is True
    worker.join(timeout=3)

    assert not worker.is_alive()
    assert errors and isinstance(errors[0], AgentCancelledError)
    conversation = service.get_conversation("cancel-thread")
    assert conversation is not None
    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "user"


def test_build_agent_accepts_injected_model() -> None:
    agent = build_archwise_agent(
        model=fake_hypothesis_model(["ok"]),
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {
            "uncertainty": "hello",
            "messages": [HumanMessage(content="hello")],
        },
        {"configurable": {"thread_id": "thread-2"}},
    )

    assert result["result"].hypothesis.statement == "ok"
    assert result["result"].uncertainty == "hello"
